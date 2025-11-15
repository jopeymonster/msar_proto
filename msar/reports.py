# -*- coding: utf-8 -*-
# msar/reports.py

from __future__ import annotations
import csv
from csv import writer
from pathlib import Path
from typing import List, Tuple

from bingads.authorization import AuthorizationData
from bingads.service_client import ServiceClient
from bingads.v13.reporting import (
    ReportingServiceManager,
    ReportingDownloadParameters
)


# -----------------------------
# Helpers
# -----------------------------

def date_fix(ymd: str) -> Tuple[str, str, str]:
    """
    Convert 'YYYY-MM-DD' or 'YYYYMMDD' into (YYYY, MM, DD).
    """
    ymd = ymd.replace("-", "")
    return (ymd[0:4], ymd[4:6], ymd[6:8])


def _build_report_request(
    reporting_service: ServiceClient,
    account_id: int,
    start_ymd: Tuple[str, str, str],
    end_ymd: Tuple[str, str, str],
    report_name: str,
):
    factory = reporting_service.factory

    # Base request
    req = factory.create("CampaignPerformanceReportRequest")
    req.ReportName = report_name
    req.Format = "Csv"
    req.ReturnOnlyCompleteData = False
    req.Aggregation = "Daily"

    # Scope
    scope = factory.create("AccountThroughCampaignReportScope")
    scope.AccountIds = {"long": [account_id]}
    scope.Campaigns = None
    req.Scope = scope

    # Time
    time = factory.create("ReportTime")
    time.CustomDateRangeStart = {
        "Day": int(start_ymd[2]),
        "Month": int(start_ymd[1]),
        "Year": int(start_ymd[0]),
    }
    time.CustomDateRangeEnd = {
        "Day": int(end_ymd[2]),
        "Month": int(end_ymd[1]),
        "Year": int(end_ymd[0]),
    }
    time.PredefinedTime = None
    time.ReportTimeZone = "PacificTimeUSCanadaTijuana"
    req.Time = time

    # ✅ Columns – this is the critical part
    cols = factory.create("ArrayOfCampaignPerformanceReportColumn")
    cols.CampaignPerformanceReportColumn.append([
        "TimePeriod",
        "AccountId",
        "AccountName",
        "CampaignId",
        "CampaignName",
        "CampaignType",
        "Impressions",
        "Clicks",
        "Spend",
    ])
    req.Columns = cols

    return req



# -----------------------------
# Main report process
# -----------------------------

def run_campaign_performance_report(
    authorization_data: AuthorizationData,
    account_list: List[dict],  # full account objects
    start_date_str: str,
    end_date_str: str,
    out_dir: Path,
    file_name: str,
) -> Path:
    """
    Download campaign performance CSVs for one or more accounts,
    merge into a single CSV, and return the merged file path.
    """

    svc_mgr = ReportingServiceManager(
        authorization_data=authorization_data,
        poll_interval_in_milliseconds=1000,
    )

    if authorization_data.authentication is None:
        raise ValueError("authorization_data.authentication cannot be None")

    env = authorization_data.authentication.environment
    reporting_service = ServiceClient(
        service="ReportingService",
        version=13,
        authorization_data=authorization_data,
        environment=env,
    )

    start_ymd = date_fix(start_date_str)
    end_ymd = date_fix(end_date_str)

    out_path = out_dir / file_name
    header_written = False

    with out_path.open("w", newline="", encoding="utf-8") as merged_file:
        w = writer(merged_file)

        for acct in account_list:
            acct_id = int(acct["account_id"])
            acct_name = acct["account_name"]
            tmp_path = out_dir / f"temp_{acct_id}.csv"

            print(f"Running report for {acct_name} - {acct_id}...")

            request = _build_report_request(
                reporting_service=reporting_service,
                account_id=acct_id,
                start_ymd=start_ymd,
                end_ymd=end_ymd,
                report_name=f"MSAR_{acct_id}",
            )

            params = ReportingDownloadParameters(
                report_request=request,
                result_file_directory=str(out_dir),
                result_file_name=f"temp_{acct_id}.csv",
                overwrite_result_file=True,
            )

            try:
                svc_mgr.download_file(params)
            except Exception as ex:
                print(
                    f"  x - Error downloading for {acct_name} ({acct_id}). Skipping."
                )
                # If you want more detail while debugging:
                # print(f"    Details: {ex}")
                continue

            if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                print(f"  x - No file created for {acct_name}. Skipping.")
                continue

            with tmp_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.reader(f))

            if not rows:
                print(f"  x - Empty file for {acct_name}. Skipping.")
                continue

            header_idx = next(
                (i for i, r in enumerate(rows) if r and r[0].startswith("TimePeriod")),
                None,
            )
            if header_idx is None:
                print(f"  x - Invalid header for {acct_name}. Skipping.")
                continue

            header = rows[header_idx]
            data_rows = []

            for r in rows[header_idx + 1 :]:
                if "Microsoft Corporation" in " ".join(r):
                    break
                data_rows.append(r)

            if not header_written:
                w.writerow(header)
                header_written = True

            if data_rows:
                w.writerows(data_rows)
                print(f"  - {len(data_rows)} rows added from {acct_name}.")
            else:
                print(f"  x - No data rows for {acct_name}. Skipping.")

            tmp_path.unlink(missing_ok=True)

    return out_path


# -----------------------------
# Load + clean merged file
# -----------------------------

def load_report_rows(csv_path: Path):
    cleaned = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            cleaned.append([c.replace("Ôªø", "").strip() for c in r])

    header_idx = next(
        (i for i, row in enumerate(cleaned) if row and row[0].startswith("TimePeriod")),
        None,
    )
    if header_idx is None:
        return [], []

    header = cleaned[header_idx]
    data = []

    for row in cleaned[header_idx + 1 :]:
        if "Microsoft Corporation" in " ".join(row):
            break
        data.append(row)

    return header, data


def save_clean_report_only(raw_path: Path, headers, rows):
    clean_path = raw_path.with_name(f"{raw_path.stem}_CLEAN.csv")

    with clean_path.open("w", newline="", encoding="utf-8") as f:
        w = writer(f)
        w.writerow(headers)
        w.writerows(rows)

    raw_path.unlink(missing_ok=True)
    print(f"\nCleaned report saved to:\n {clean_path}\n")

    return clean_path
