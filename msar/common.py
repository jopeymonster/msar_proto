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
from typing import Any, Dict, Optional

from tabulate import tabulate

# -----------------------------
# Builtins monkey-patch for input "exit"
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
# Micro-unit helpers
# -----------------------------
MICROS_PER_UNIT = Decimal("1000000")

def micros_to_decimal(
    micros: Optional[int | str],
    quantize: Optional[Decimal] = None,
    rounding=ROUND_HALF_UP,
) -> Decimal:
    if micros in (None, ""):
        value = Decimal("0")
    else:
        value = Decimal(str(micros)) / MICROS_PER_UNIT
    return value.quantize(quantize, rounding=rounding) if quantize else value


# -----------------------------
# Simple console / CSV output
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
) -> None:
    if not table_data or not headers:
        print("No data to display.")
        return

    report_view = preselected_output
    if not report_view:
        print("How would you like to view the report?\n1. CSV\n2. Display table on screen\n")
        report_view = input("Choose 1 or 2 ('exit' to quit): ").strip().lower()

    if report_view in ("1", "csv"):
        save_csv(table_data, headers)
    elif report_view in ("2", "table"):
        display_table(table_data, headers)
    elif report_view == "auto":
        display_table(table_data, headers, auto_view=True)
    else:
        print("Invalid option.")
        sys.exit(1)


# -----------------------------
# Date utilities (unchanged)
# -----------------------------
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%Y%m%d")
def parse_supported_date(date_str: str) -> date:
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except (TypeError, ValueError):
            continue
    raise ValueError(f"Unsupported date format: {date_str}")

def validate_date_input(date_str: Optional[str], default_today: bool = False) -> Optional[str]:
    if not date_str:
        if default_today:
            today_str = date.today().strftime("%Y-%m-%d")
            print(f"No date entered. Defaulting to today's date: {today_str}")
            return today_str
        print("Invalid date format. Use YYYY-MM-DD or YYYYMMDD.")
        return None
    try:
        parse_supported_date(date_str)
        return date_str
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD or YYYYMMDD.")
        return None

def get_last30days() -> tuple[str, date, date, str]:
    today = date.today()
    return "Date range", today - timedelta(days=30), today - timedelta(days=1), "date"

def get_timerange(force_single: bool = False) -> tuple[str, str | date, str | date, str]:
    """Prompt for a single date or range, with validation."""
    if force_single:
        date_opt = "Specific date"
        print("The report you selected only accepts a single date.")
        spec_date_input = input("Enter the date (YYYY-MM-DD or YYYYMMDD) or leave blank and press ENTER: ").strip()
        spec_date = validate_date_input(spec_date_input, default_today=True)
        return date_opt, spec_date, spec_date, "date"

    print("Reporting time range:\n1. Specific date\n2. Range of dates\n")
    opt = input("Enter 1 or 2: ").strip()
    if opt == "1":
        date_opt = "Specific date"
        spec_date = validate_date_input(input("Date (YYYY-MM-DD): ").strip(), default_today=True)
        return date_opt, spec_date, spec_date, "date"
    elif opt == "2":
        start = validate_date_input(input("Enter the Start Date (YYYY-MM-DD or YYYYMMDD)\nor leave blank and press ENTER for today:  ").strip(), default_today=True)
        end = validate_date_input(input("Enter the End Date (YYYY-MM-DD or YYYYMMDD)\nor leave blank and press ENTER for today:  ").strip(), default_today=True)
        return "Date range", start, end, "date"
    else:
        print("Invalid option.")
        return "Date range", date.today(), date.today(), "date"


# -----------------------------
# Table printer for accounts
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

    print("\nMicrosoft Ads - Managed Accounts\n")
    print(tabulate(table_data, headers=headers, tablefmt="rounded_outline"))