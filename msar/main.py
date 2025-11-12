# -*- coding: utf-8 -*-
# main.py

from __future__ import annotations
import argparse
from csv import writer
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from auth import init_authorization
from accounts import list_user_accounts
from common import (
    print_accounts_table,
    get_timerange,
    data_handling_options,
)
from reports import run_campaign_performance_report, load_report_rows


def select_accounts(accounts: List[Dict], cli_arg: str | None) -> List[int]:
    """Determine selected account IDs from CLI flag or interactive prompt."""
    if cli_arg:
        cli_arg = cli_arg.strip().lower()
        if cli_arg == "all":
            return [a["account_id"] for a in accounts]
        else:
            try:
                acc_id = int(cli_arg)
                match = [a["account_id"] for a in accounts if a["account_id"] == acc_id]
                if match:
                    return match
                print(f"No account with ID {acc_id} found. Defaulting to all.")
                return [a["account_id"] for a in accounts]
            except ValueError:
                print("Invalid --account argument. Defaulting to all.")
                return [a["account_id"] for a in accounts]

    # Interactive selection
    while True:
        selection = input("\nEnter the number of an account to run, or 'all' for all accounts: ").strip().lower()
        if selection in ("all", "a"):
            return [a["account_id"] for a in accounts]
        try:
            idx = int(selection)
            if 1 <= idx <= len(accounts):
                return [accounts[idx - 1]["account_id"]]
        except ValueError:
            pass
        print("Invalid selection. Please try again.")


def handle_report_outputs(
        raw_path: Path,
        headers: List[str],
        rows: List[List[str]],
        clean_mode: str | None,
        auto_view: bool,
) -> None:
    """Save report files and present post-processing options based on --clean mode.

    The clean_mode flag accepts three values:
    - "both": keep the downloaded raw CSV and write a cleaned version.
    - "exclude": keep only the raw CSV, matching the default CLI behavior.
    - "only": write the cleaned CSV then remove the raw download.
    """
    mode = clean_mode or "exclude"
    explicit_mode = clean_mode is not None
    clean_path = raw_path.with_name(f"{raw_path.stem}_CLEAN.csv")
    raw_saved = mode in ("both", "exclude")
    clean_saved = mode in ("both", "only")

    if clean_saved:
        with clean_path.open("w", newline="", encoding="utf-8") as file:
            w = writer(file)
            w.writerow(headers)
            w.writerows(rows)

    if raw_saved:
        print(f"\nRaw report saved to: {raw_path}")
    else:
        raw_path.unlink(missing_ok=True)
        print(f"\nRaw report excluded per execution option:\n {raw_path}\n")

    if clean_saved:
        print(f"Cleaned report saved to:\n {clean_path}\n")
    elif mode == "exclude" and explicit_mode:
        print("Cleaned report excluded per execution option.")
    
    data_handling_options(
        rows,
        headers,
        auto_view=auto_view,
        preselected_output="auto" if auto_view else None,
    )

def main():
    parser = argparse.ArgumentParser(prog="MSAdsReporter", description="Microsoft Ads Reporting CLI")
    parser.add_argument("--config", required=True, help="Path to config/auth_info.json")
    parser.add_argument("--account", help="Specify account ID or 'all'")
    parser.add_argument("--auto", action="store_true", help="Auto-view results without prompts")
    parser.add_argument(
        "--clean", 
        choices=("both","exclude","only"),
        default="only",
        help=(
            "Controls report handling: 'both' saves raw and cleaned report files, "
            "'exclude' keeps only the raw file, 'only' keeps only the clean file."
            "\nDefault is 'only' to generate a clean report."
        ),
    )
    args = parser.parse_args()

    # --- Authenticate ---
    auth_path = Path(args.config)
    authorization_data, meta = init_authorization(auth_path)
    print(f"\nAuthenticated. Environment: {meta['environment']}. Refresh token saved: {meta['has_refresh_token']}\n")

    # --- Get accounts ---
    accounts = list_user_accounts(authorization_data)
    if not accounts:
        print("No accounts found for the current user.")
        return

    print_accounts_table(accounts)
    account_ids = select_accounts(accounts, args.account)

    # --- Report selection (placeholder) ---
    print("\nAvailable Reports:\n1. Campaign Performance")
    choice = input("Enter report number (default 1): ").strip() or "1"
    if choice != "1":
        print("Only Campaign Performance is available currently.")
    print("Selected: Campaign Performance\n")

    # --- Date range ---
    _, start_date, end_date, seg_key = get_timerange(force_single=False)
    start_date = str(start_date).replace("/", "-")
    end_date = str(end_date).replace("/", "-")

    # --- Output setup ---
    out_dir = Path.cwd() / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"msar_campaign_performance_{timestamp}.csv"

    # --- Run report for all selected accounts (single consolidated CSV) ---
    selected_account_objs = [a for a in accounts if a["account_id"] in account_ids]

    print(f"\nRunning Campaign Performance report for {len(selected_account_objs)} account(s)...\n")

    out_csv = run_campaign_performance_report(
        authorization_data=authorization_data,
        account_list=selected_account_objs,
        start_date_str=start_date,
        end_date_str=end_date,
        seg_key=seg_key,
        out_dir=out_dir,
        file_name=base_filename,
    )

    headers, rows = load_report_rows(out_csv)
    if not rows:
        print("No data returned for the selected range.")
        return

    # --- Output ---
    handle_report_outputs(
        raw_path=out_csv,
        headers=headers,
        rows=rows,
        clean_mode=args.clean,
        auto_view=args.auto,
    )

    print("\nAll requested reports complete.\n")


if __name__ == "__main__":
    main()