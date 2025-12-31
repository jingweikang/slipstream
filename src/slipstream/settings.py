from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    STRAVA_CLIENT_ID: int
    STRAVA_CLIENT_SECRET: str
    STRAVA_REDIRECT_URI: str = "http://localhost:8000/auth/callback"

    STRAVA_ACCESS_TOKEN: str | None = None
    STRAVA_REFRESH_TOKEN: str | None = None
    STRAVA_EXPIRES_AT: int | None = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
