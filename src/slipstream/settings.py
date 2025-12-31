from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    STRAVA_CLIENT_ID: int
    STRAVA_CLIENT_SECRET: str
    STRAVA_REDIRECT_URI: str = "http://localhost:8000/auth/callback"

    STRAVA_ACCESS_TOKEN: Optional[str] = None
    STRAVA_REFRESH_TOKEN: Optional[str] = None
    STRAVA_EXPIRES_AT: Optional[int] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
