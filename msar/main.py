# -*- coding: utf-8 -*-
# msar/main.py

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Import pattern allowing script OR package mode
try:
    from .auth import init_authorization
    from .accounts import list_user_accounts
    from .common import print_accounts_table, get_timerange, data_handling_options
    from .reports import (
        run_campaign_performance_report,
        load_report_rows,
        save_clean_report_only,
    )
except ImportError:
    from auth import init_authorization
    from accounts import list_user_accounts
    from common import print_accounts_table, get_timerange, data_handling_options
    from reports import (
        run_campaign_performance_report,
        load_report_rows,
        save_clean_report_only,
    )


def select_accounts(accounts: List[Dict], cli_arg: str | None) -> List[int]:
    """Return list of account_ids based on CLI or user prompt."""
    if cli_arg:
        cli_arg = cli_arg.strip().lower()
        if cli_arg == "all":
            return [a["account_id"] for a in accounts]

        try:
            acc_id = int(cli_arg)
            ids = [a["account_id"] for a in accounts]
            if acc_id in ids:
                return [acc_id]
            print(f"No account with ID {acc_id}. Defaulting to ALL.")
        except ValueError:
            print("Invalid --account value. Defaulting to ALL.")

        return [a["account_id"] for a in accounts]

    # interactive
    while True:
        choice = input("\nEnter account # or 'all': ").strip().lower()
        if choice in ("all", "a"):
            return [a["account_id"] for a in accounts]
        try:
            i = int(choice)
            if 1 <= i <= len(accounts):
                return [accounts[i - 1]["account_id"]]
        except ValueError:
            pass
        print("Invalid selection. Try again.")


def main():
    parser = argparse.ArgumentParser(prog="MSAdsReporter")
    parser.add_argument("--config", required=True)
    parser.add_argument("--account")
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    # ---- Authenticate ----
    auth_path = Path(args.config)
    authorization_data, meta = init_authorization(auth_path)
    print(
        f"\nAuthenticated. Environment: {meta['environment']} "
        f"(refresh token saved: {meta['has_refresh_token']})\n"
    )

    # ---- Accounts ----
    accounts = list_user_accounts(authorization_data)
    print_accounts_table(accounts)

    selected_ids = select_accounts(accounts, args.account)
    selected_objs = [a for a in accounts if a["account_id"] in selected_ids]

    # ---- Report selection ----
    print("\nAvailable Reports:\n1. Campaign Performance")
    choice = input("Enter report number (default 1): ").strip() or "1"
    print("Selected: Campaign Performance\n")

    # ---- Output preference (before running reports) ----
    if args.auto:
        output_pref = "auto"
    else:
        print("How would you like to view the results when the report completes?")
        print("1. Save as CSV")
        print("2. Display table on screen")
        print("3. Save CSV and display table")
        view_choice = input("Choose 1, 2, or 3 (default 1): ").strip() or "1"

        if view_choice == "2":
            output_pref = "table"
        elif view_choice == "3":
            output_pref = "both"
        else:
            output_pref = "csv"

    # ---- Date selection ----
    _, start_date_str, end_date_str, seg_key_ignored = get_timerange()

    # ---- Output dirs ----
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"msar_campaign_performance_{now}.csv"

    print(f"\nRunning Campaign Performance report for {len(selected_objs)} account(s)...\n")

    # ---- Run report ----
    out_csv = run_campaign_performance_report(
        authorization_data=authorization_data,
        account_list=selected_objs,
        start_date_str=start_date_str,
        end_date_str=end_date_str,
        out_dir=out_dir,
        file_name=file_name,
    )

    headers, rows = load_report_rows(out_csv)
    if not rows:
        print("No data returned for selected range.")
        return

    clean_path = save_clean_report_only(out_csv, headers, rows)

    data_handling_options(
        table_data=rows,
        headers=headers,
        auto_view=(output_pref == "auto"),
        preselected_output=output_pref,
        saved_report_path=clean_path,
    )

    print("\nAll requested reports complete.\n")


if __name__ == "__main__":
    main()
