from typing import Any

import requests

from slipstream.ingest.auth import is_token_expired, refresh_access_token
from slipstream.settings import settings


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


def fetch_activity_streams(
    activity_id: int,
    keys: str = "time,latlng,distance,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth",
) -> dict[str, Any]:
    token = _get_bearer_token()
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keys": keys, "key_by_type": True}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def list_activities(
    per_page: int = 30,
    page: int = 1,
    before: int | None = None,
    after: int | None = None,
) -> Any:
    """List athlete activities.

    Args:
        per_page: Number of activities per page (max 200)
        page: Page number
        before: Epoch timestamp to filter activities before this time
        after: Epoch timestamp to filter activities after this time
               (results will be sorted oldest first when using after)

    Returns:
        List of activity dictionaries
    """
    token = _get_bearer_token()
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"per_page": per_page, "page": page}

    if before is not None:
        params["before"] = before
    if after is not None:
        params["after"] = after

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()
