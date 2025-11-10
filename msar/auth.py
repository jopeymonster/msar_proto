# -*- coding: utf-8 -*-
# auth.py

import json
from pathlib import Path
from typing import Tuple, Dict

from bingads.authorization import (
    AuthorizationData,
    OAuthDesktopMobileAuthCodeGrant,
    OAuthTokens
)

ENVIRONMENTS = {"production": "production", "sandbox": "sandbox"}

def load_auth_info(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def init_authorization(auth_info_path: Path) -> Tuple[AuthorizationData, Dict]:
    cfg = load_auth_info(auth_info_path)

    developer_token = cfg["developer_token"]
    client_id = cfg["client_id"]
    env = ENVIRONMENTS.get(cfg.get("environment", "production").lower(), "production")
    client_state = cfg.get("client_state", "msar")
    refresh_token = cfg.get("refresh_token") or ""
    # redirect_uri is not passed to get_authorization_endpoint for Desktop/Mobile flow

    # Build OAuth (desktop/mobile)
    oauth = OAuthDesktopMobileAuthCodeGrant(client_id=client_id, env=env)
    oauth.state = client_state

    # check for refresh token, use it; else consent.
    if refresh_token:
        # Use built-in refresh flow; don't try to assign oauth_tokens manually
        oauth.request_oauth_tokens_by_refresh_token(refresh_token)
    else:
        # IMPORTANT: no args here
        auth_url = oauth.get_authorization_endpoint()
        print("\nOpen this URL and sign in to grant access:\n")
        print(auth_url)

        print("\nAfter granting access, paste redirect URL into redirect.txt, then press Enter")
        input("Press Enter when ready... ")
        with open("redirect.txt", "r", encoding="utf-8") as f:
            response_uri = f.read().strip()

        oauth.request_oauth_tokens_by_response_uri(response_uri=response_uri)

        # Persist refresh token for next runs
        cfg["refresh_token"] = oauth.oauth_tokens.refresh_token
        with auth_info_path.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    authorization_data = AuthorizationData(
        account_id=None,
        customer_id=None,
        developer_token=developer_token,
        authentication=oauth
    )

    meta = {
        "environment": env,
        "has_refresh_token": bool(oauth.oauth_tokens and oauth.oauth_tokens.refresh_token)
    }
    return authorization_data, meta
