from __future__ import annotations

import time
from typing import Any

import requests

TOKEN_URL = "https://www.strava.com/oauth/token"


def build_authorization_url(
    client_id: str, redirect_uri: str, scope: str = "activity:read_all"
) -> str:
    return (
        f"https://www.strava.com/oauth/authorize?client_id={client_id}"
        f"&response_type=code&redirect_uri={redirect_uri}&scope={scope}&approval_prompt=auto"
    )


def exchange_code_for_token(
    code: str, client_id: str, client_secret: str
) -> dict[str, Any]:
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    refresh_token: str, client_id: str, client_secret: str
) -> dict[str, Any]:
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    resp.raise_for_status()
    return resp.json()


def is_token_expired(expires_at: int, buffer: int = 60) -> bool:
    now = int(time.time())
    return expires_at <= now + buffer
