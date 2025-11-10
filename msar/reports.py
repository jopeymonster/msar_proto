from typing import Iterable, List
from pathlib import Path
from bingads.service_client import ServiceClient
from bingads.authorization import AuthorizationData

def campaign_performance_report(
    authorization_data: AuthorizationData,
    account_ids: Iterable[int],
    aggregation: str = "Daily",   # Summary, Daily, Weekly, Monthly, etc.
    start_date=(2024, 1, 1),      # (Y, M, D) or use predefined time instead
    end_date=(2024, 12, 31),
    report_name: str = "CampaignPerformance"
) -> Path:
    """
    Requests a CampaignPerformance report across many accounts, downloads the zipped CSV,
    and returns the local path to the ZIP.
    """
    env = authorization_data.authentication.environment
    reporting = ServiceClient(
        service='ReportingService',
        version=13,
        authorization_data=authorization_data,
        environment=env
    )

    request = reporting.factory.create('ns5:CampaignPerformanceReportRequest')
    request.Format = 'Csv'
    request.FormatVersion = '2.0'
    request.ReportName = report_name
    request.ReturnOnlyCompleteData = False
    request.Aggregation = aggregation

    # Columns — include time + your metrics
    # (Exact enum names per docs)
    request.Columns = {'CampaignPerformanceReportColumn': [
        'TimePeriod',
        'AccountId', 'AccountName',
        'CampaignId', 'CampaignName', 'CampaignType',
        'Impressions', 'Clicks', 'Spend'
    ]}

    scope = reporting.factory.create('ns5:AccountThroughCampaignReportScope')
    scope.AccountIds = {'long': list({int(a) for a in account_ids})}
    scope.Campaigns = None
    request.Scope = scope

    time = reporting.factory.create('ns5:ReportTime')
    start = reporting.factory.create('ns5:Date')
    start.Year, start.Month, start.Day = start_date
    end = reporting.factory.create('ns5:Date')
    end.Year, end.Month, end.Day = end_date
    time.CustomDateRangeStart = start
    time.CustomDateRangeEnd = end
    time.ReportTimeZone = 'PacificTimeUSCanadaTijuana'
    request.Time = time

    submit = reporting.SubmitGenerateReport(ReportRequest=request)
    report_request_id = submit.ReportRequestId

    # Poll until complete, then download using SDK helper (left out for brevity)
    # We’ll fill in: GetReportDownloadUrl -> stream to file -> return that Path.
    # See the "Report Requests Code Example" for the full loop. 
    return Path("REPORT_TODO.zip")
