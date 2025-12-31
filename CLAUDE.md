# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Slipstream analyzes cycling performance data from Strava to detect fatigue patterns and improve FTP (Functional Threshold Power) and pacing strategy. The system will eventually use Spark for batch analysis and Flink for real-time stream processing.

Currently in Phase 0 (Authentication & Data Ingestion).

## Development Commands

```bash
# Install dependencies
poetry install

# Start OAuth flow (prints URL to visit)
poetry run python scripts/cli.py auth-start

# Exchange auth code for tokens
poetry run python scripts/cli.py auth-exchange <code>

# Fetch activities (requires tokens set in env)
poetry run python scripts/cli.py fetch-activities --per-page 30 --page 1

# Fetch stream data for an activity
poetry run python scripts/cli.py fetch-stream <activity_id>

# Run tests
poetry run pytest
```

## Code Architecture

### Authentication Flow

Single-user OAuth implementation with stateless, environment-based credential storage:

- **OAuth helpers** (`src/slipstream/ingest/auth.py`): Pure functions for authorization URL generation, code exchange, and token refresh. No file I/O or side effects.
- **Credential storage**: All tokens stored as environment variables (CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN, EXPIRES_AT)
- **Token refresh**: Automatic in-memory refresh when tokens expire. Refreshed tokens persist only for the duration of the Python process.

### Data Ingestion

- **Strava API client** (`src/slipstream/ingest/strava.py`): Fetches activity lists and stream data (HR, power, cadence, altitude, GPS)
- **Token management**: `_get_bearer_token()` reads from settings, auto-refreshes if expired, updates settings in-memory
- **Stream keys**: `heartrate`, `watts`, `cadence`, `altitude`, `latlng`

### Configuration

- **Settings** (`src/slipstream/settings.py`): Pydantic v2 with pydantic-settings
- **Supports**: Environment variables and `.env` file
- **Required fields**: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
- **Optional fields**: STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN, STRAVA_EXPIRES_AT (set after OAuth flow)

### CLI

Single entry point using Click framework (`scripts/cli.py`). All commands use the `settings` object directly for configuration.

## Key Patterns

**Stateless credential management**: Credentials stored in environment variables only. Perfect for Docker deployment. No file I/O for tokens.

**In-memory token refresh**: When tokens expire during a process run, they're automatically refreshed and stored in-memory. Next process uses original env vars. Works well for short-lived CLI commands and containerized batch jobs.

**Settings-first configuration**: Single `settings` object is the source of truth. All modules import and use it directly.

## Technical Stack

- Python 3.11+
- Poetry (dependency management)
- Pydantic v2 + pydantic-settings (configuration)
- Click (CLI framework)
- requests (HTTP client)
