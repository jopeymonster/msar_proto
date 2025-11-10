# -*- coding: utf-8 -*-
# main.py

import argparse
from pathlib import Path

from auth import init_authorization
from accounts import list_user_accounts
from common import print_accounts_table

def main():
    parser = argparse.ArgumentParser(prog="MSAdsReporter", description="Microsoft Ads Reporting CLI")
    parser.add_argument("--config", required=True, help="Path to config/auth_info.json")
    args = parser.parse_args()

    auth_path = Path(args.config)
    authorization_data, meta = init_authorization(auth_path)

    print(f"\nAuthenticated. Environment: {meta['environment']}. Refresh token saved: {meta['has_refresh_token']}\n")

    accounts = list_user_accounts(authorization_data)
    if not accounts:
        print("No accounts found for the current user.")
        return

    print_accounts_table(accounts)

if __name__ == "__main__":
    main()