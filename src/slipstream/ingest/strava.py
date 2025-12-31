from typing import Dict, Any
import requests
from slipstream.settings import settings
from slipstream.ingest.auth import refresh_access_token, is_token_expired


def _get_bearer_token() -> str:
    if not settings.STRAVA_ACCESS_TOKEN:
        raise RuntimeError(
            "No access token found. Run the auth flow and set STRAVA_ACCESS_TOKEN, "
            "STRAVA_REFRESH_TOKEN, and STRAVA_EXPIRES_AT environment variables."
        )

    if settings.STRAVA_EXPIRES_AT and is_token_expired(settings.STRAVA_EXPIRES_AT):
        if not settings.STRAVA_REFRESH_TOKEN:
            raise RuntimeError("Token expired and no refresh token available.")

        new_tokens = refresh_access_token(
            settings.STRAVA_REFRESH_TOKEN,
            str(settings.STRAVA_CLIENT_ID),
            settings.STRAVA_CLIENT_SECRET,
        )

        settings.STRAVA_ACCESS_TOKEN = new_tokens["access_token"]
        settings.STRAVA_REFRESH_TOKEN = new_tokens["refresh_token"]
        settings.STRAVA_EXPIRES_AT = new_tokens["expires_at"]

    return settings.STRAVA_ACCESS_TOKEN


def fetch_activity_streams(activity_id: int) -> Dict[str, Any]:
    token = _get_bearer_token()
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keys": "heartrate,watts,cadence,altitude,latlng", "key_by_type": True}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def list_activities(per_page: int = 30, page: int = 1) -> Any:
    token = _get_bearer_token()
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"per_page": per_page, "page": page}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()
