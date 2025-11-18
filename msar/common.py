# -*- coding: utf-8 -*-
# msar/common.py

"""
Shared constants and utility helpers for CLI parsing, data handling, and reporting.
"""

from __future__ import annotations
import csv, pydoc, re, sys
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Optional

from tabulate import tabulate

# -----------------------------
# monkey-patch input "exit"
# -----------------------------
def _custom_input(prompt: str = "") -> str:
    user_input = _original_input(prompt)
    if user_input.lower() == "exit":
        print("Exiting the program.")
        sys.exit()
    return user_input

if isinstance(__builtins__, dict):
    _original_input = __builtins__["input"]
    __builtins__["input"] = _custom_input
else:
    _original_input = __builtins__.input
    __builtins__.input = _custom_input


# -----------------------------
# console / CSV output
# -----------------------------
def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", name)

def save_csv(table_data, headers, prefix: str = "msar_report") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_file_name = f"{prefix}_{timestamp}.csv"
    print(f"Default file name: {default_file_name}")
    file_name_input = input("Enter a file name (or leave blank for default): ").strip()
    base_name = sanitize_filename(file_name_input.replace(".csv", "")) or default_file_name
    file_path = Path.home() / (base_name if base_name.endswith(".csv") else f"{base_name}.csv")

    try:
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(table_data)
        print(f"\nData saved to: {file_path}\n")
    except Exception as e:
        print(f"\nFailed to save file: {e}\n")

def display_table(table_data, headers, auto_view: bool = False) -> None:
    table_txt = tabulate(table_data, headers, tablefmt="simple_grid")
    if auto_view:
        print(table_txt)
    else:
        input("Press ENTER to view table; 'Q' to exit output when done...")
        pydoc.pager(table_txt)

def data_handling_options(
    table_data,
    headers,
    auto_view: bool = False,
    preselected_output: Optional[str] = None,
    saved_report_path: Optional[Path] = None,
) -> None:
    if not table_data or not headers:
        print("No data to display.")
        return

    mode = (preselected_output or "").strip().lower()

    # interactive mode
    if not mode:
        print("How would you like to view the report?\n1. CSV\n2. Display table on screen\n")
        choice = input("Choose 1 or 2 ('exit' to quit): ").strip().lower()
        if choice in ("1", "csv"):
            mode = "csv"
        elif choice in ("2", "table"):
            mode = "table"
        else:
            print("Invalid option.")
            sys.exit(1)

    if mode == "auto":
        display_table(table_data, headers, auto_view=True)
        return

    if mode == "csv":
        if saved_report_path:
            print(f"\nClean report saved to: {saved_report_path}")
            return
        save_csv(table_data, headers)
        return

    if mode == "table":
        display_table(table_data, headers, auto_view=auto_view)
        return

    if mode == "both":
        if saved_report_path:
            print(f"\nClean report saved to: {saved_report_path}")
        display_table(table_data, headers, auto_view=auto_view)
        return

    # fallback
    display_table(table_data, headers, auto_view=auto_view)


# -----------------------------
# dateutils
# -----------------------------
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%Y%m%d")

def parse_supported_date(date_str: str) -> date:
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except (TypeError, ValueError):
            continue
    raise ValueError(f"Unsupported date format: {date_str}")

def validate_date_input(date_str: Optional[str], default_today: bool = False) -> Optional[date]:
    if not date_str:
        if default_today:
            today = date.today()
            print(f"No date entered. Defaulting to today's date: {today}")
            return today
        print("Invalid date format. Use YYYY-MM-DD or YYYYMMDD.")
        return None
    try:
        return parse_supported_date(date_str)
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD or YYYYMMDD.")
        return None

def _prompt_for_date(prompt: str, default_today: bool = False) -> date:
    while True:
        entered = input(prompt).strip()
        parsed = validate_date_input(entered, default_today=default_today)
        if parsed is not None:
            return parsed

def get_last30days() -> tuple[str, date, date, str]:
    today = date.today()
    return "Date range", today - timedelta(days=30), today - timedelta(days=1), "date"

def get_timerange(force_single: bool = False) -> tuple[str, str, str, str]:
    """
    Prompt for a single date or range of dates and ALWAYS return:
        (label, start_date_str, end_date_str, seg_key)

    Dates are normalized to 'YYYY-MM-DD' strings before returning.
    """
    def _normalize_date_obj(d):
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        return str(d)

    # forced single date
    if force_single:
        date_opt = "Specific date"
        print("\nThe report you selected only accepts a single date.")
        spec_date = _prompt_for_date(
            "Enter the date (YYYY-MM-DD or YYYYMMDD) or press ENTER for today: ",
            default_today=True,
        )
        nd = _normalize_date_obj(spec_date)
        return date_opt, nd, nd, "date"

    print("\nReporting time range:\n1. Specific date\n2. Range of dates")
    opt = input("Enter 1 or 2: ").strip()

    # single date
    if opt == "1":
        date_opt = "Specific date"
        spec_date = _prompt_for_date(
            "Date (YYYY-MM-DD or YYYYMMDD): ",
            default_today=True,
        )
        nd = _normalize_date_obj(spec_date)
        return date_opt, nd, nd, "date"

    # date range
    if opt == "2":
        start = _prompt_for_date(
            "Enter the Start Date (YYYY-MM-DD or YYYYMMDD) or press ENTER for today: ",
            default_today=True,
        )
        end = _prompt_for_date(
            "Enter the End Date (YYYY-MM-DD or YYYYMMDD) or press ENTER for today: ",
            default_today=True,
        )
        return "Date range", _normalize_date_obj(start), _normalize_date_obj(end), "date"

    # fallback
    print("Invalid option. Defaulting to today's date.")
    today_str = date.today().strftime("%Y-%m-%d")
    return "Date range", today_str, today_str, "date"


# -----------------------------
# accounts table display
# -----------------------------
def print_accounts_table(items):
    """Display accounts with index numbers for user selection."""

    headers = ["#", "Account Name", "Account ID", "Customer ID", "Account Number"]
    table_data = []
    for idx, it in enumerate(items, start=1):
        table_data.append([
            idx,
            it["account_name"],
            str(it["account_id"]),
            str(it["parent_customer_id"]),
            it["number"] or ""
        ])

    print("Microsoft Ads - Managed Accounts\n")
    print(tabulate(table_data, headers=headers, tablefmt="rounded_outline"))
