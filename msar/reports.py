# -*- coding: utf-8 -*-
# msar/reports.py

from __future__ import annotations
import csv
from csv import writer
import time
from pathlib import Path
from typing import Iterable, List, Tuple, Optional, Dict, TypedDict

from bingads.authorization import AuthorizationData
from bingads.service_client import ServiceClient
from bingads.v13.reporting import ReportingServiceManager, ReportingDownloadParameters


# timedate SDK enums mapping
_AGG_MAP = {
    "date": "Daily",
    "week": "Weekly",
    "month": "Monthly",
    "quarter": "Quarterly",
    "year": "Yearly",
}

def _build_report_request(
    svc_mgr,
    account_ids: Iterable[int],
    start_date: Tuple[int, int, int],
    end_date: Tuple[int, int, int],
    aggregation_key: str = "date",
    report_name: str = "MSAR_Campaign_Performance",
    time_zone: str = "PacificTimeUSCanadaTijuana",
):
    """
    Builds a CampaignPerformanceReportRequest object using the service factory.
    """
    reporting_service = ServiceClient(
        service="ReportingService",
        version=13,
        authorization_data=svc_mgr._authorization_data,
        environment=svc_mgr._environment
        )
    factory = reporting_service.factory

    req = factory.create("CampaignPerformanceReportRequest")
    req.ReportName = report_name
    req.Aggregation = _AGG_MAP.get(aggregation_key, "Daily")
    req.Format = "Csv"
    req.ReturnOnlyCompleteData = False
    req.FormatVersion = "2.0"

    req.Columns = {
        "CampaignPerformanceReportColumn": [
            "TimePeriod",
            "AccountId",
            "AccountName",
            "CampaignId",
            "CampaignName",
            "CampaignType",
            "Impressions",
            "Clicks",
            "Spend",
        ]
    }

    scope = factory.create("AccountThroughCampaignReportScope")
    scope.AccountIds = {"long": list({int(a) for a in account_ids})}
    scope.Campaigns = None
    req.Scope = scope

    time = factory.create("ReportTime")
    s = factory.create("Date")
    s.Year, s.Month, s.Day = start_date
    e = factory.create("Date")
    e.Year, e.Month, e.Day = end_date
    time.CustomDateRangeStart = s
    time.CustomDateRangeEnd = e
    time.ReportTimeZone = time_zone
    req.Time = time

    return req


def run_campaign_performance_report(
    authorization_data: AuthorizationData,
    account_list: Iterable[Dict],
    start_date_str: str,
    end_date_str: str,
    seg_key: str = "date",
    out_dir: Optional[Path] = None,
    file_name: str = "msar_campaign_performance.csv",
) -> Path:
    """
    Downloads Campaign Performance CSVs for one or more accounts,
    logs progress per account, combines all valid results into one file.
    """

    if authorization_data.authentication is None:
        raise ValueError("authorization_data.authentication cannot be None")
    env = authorization_data.authentication.environment
    svc_mgr = ReportingServiceManager(
        authorization_data=authorization_data,
        poll_interval_in_milliseconds=5000,
        environment=env,
    )

    def _split(d: str) -> Tuple[int, int, int]:
        """
        Removes hyphen from date input for processing.
        """
        ds = d.replace("-", "")
        return (int(ds[0:4]), int(ds[4:6]), int(ds[6:8]))

    s_ymd = _split(start_date_str)
    e_ymd = _split(end_date_str)

    out_dir = out_dir or Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / file_name

    all_headers: List[str] = []
    all_rows: List[List[str]] = []

    for acct in account_list:
        acct_id = acct["account_id"]
        acct_name = acct["account_name"]
        tmp_path = out_dir / f"temp_{acct_id}.csv"

        print(f"Running report for {acct_name} ({acct_id})...")

        # build and download
        req = _build_report_request(
            svc_mgr,
            [acct_id],
            start_date=s_ymd,
            end_date=e_ymd,
            aggregation_key=seg_key,
        )

        dl_params = ReportingDownloadParameters(
            report_request=req,
            result_file_directory=str(out_dir),
            result_file_name=tmp_path.name,
            overwrite_result_file=True,
        )

        try:
            svc_mgr.download_report(dl_params)
        except Exception as e:
            print(f"  x - Error while downloading {acct_name}: {e}")
            continue

        # short wait to ensure SDK flushes file
        time.sleep(0.5)

        if not tmp_path.exists():
            print(f"  x - No file created for {acct_name}. Skipping.")
            continue

        headers, rows = load_report_rows(tmp_path)
        if not rows:
            print(f"  x - No rows returned for {acct_name}.")
            tmp_path.unlink(missing_ok=True)
            continue

        if not all_headers:
            all_headers = headers
        all_rows.extend(rows)
        tmp_path.unlink(missing_ok=True)

        print(f"  - {len(rows)} rows added from {acct_name}.")

    # write combined CSV
    if not all_rows:
        print("\nNo valid report data returned for any accounts.")
        return csv_path

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = writer(f)
        w.writerow(all_headers)
        w.writerows(all_rows)

    return csv_path



def load_report_rows(csv_path: Path) -> Tuple[List[str], List[List[str]]]:
    """
    Load a Microsoft Ads report CSV, strip metadata/header/footer lines,
    and fix encoding artifacts.
    """
    cleaned_rows = []
    with csv_path.open("r", newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            # Strip empty rows and normalize weird characters
            if not row or all(not c.strip() for c in row):
                continue
            fixed = [c.replace("Ôªø", "").replace("¬¢", "¢").strip() for c in row]
            cleaned_rows.append(fixed)

    # Find where the actual header begins
    header_index = None
    for i, row in enumerate(cleaned_rows):
        if row and row[0].strip().startswith("TimePeriod"):
            header_index = i
            break

    if header_index is None:
        print("Could not locate report header row.")
        return [], []

    headers = cleaned_rows[header_index]
    data = []

    for row in cleaned_rows[header_index + 1 :]:
        # Stop if we reach the footer or a copyright line
        if "Microsoft Corporation" in " ".join(row):
            break
        data.append(row)

    return headers, data
