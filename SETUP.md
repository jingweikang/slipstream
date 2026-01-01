# Setup Guide

Complete setup instructions for Slipstream.

## Installation

```bash
poetry install
```

## Authentication

### 1. Get Strava API Credentials

Register your application at https://www.strava.com/settings/api to get:
- Client ID
- Client Secret

### 2. Configure Environment

Set your Strava OAuth client credentials:

```bash
export STRAVA_CLIENT_ID=<your_client_id>
export STRAVA_CLIENT_SECRET=<your_client_secret>
```

Or add them to a `.env` file in the project root:

```
STRAVA_CLIENT_ID=<your_client_id>
STRAVA_CLIENT_SECRET=<your_client_secret>
```

### 3. Run OAuth Flow

Start the OAuth authorization flow:

```bash
poetry run python scripts/cli.py auth-start
```

Visit the URL printed above, authorize the application, and copy the `code` from the redirect URL.

Exchange the code for access tokens:

```bash
poetry run python scripts/cli.py auth-exchange <code>
```

Copy the export commands from the output and run them to set your tokens:

```bash
export STRAVA_ACCESS_TOKEN=<your_access_token>
export STRAVA_REFRESH_TOKEN=<your_refresh_token>
export STRAVA_EXPIRES_AT=<timestamp>
```

Or add them to your `.env` file:

```
STRAVA_CLIENT_ID=<your_client_id>
STRAVA_CLIENT_SECRET=<your_client_secret>
STRAVA_ACCESS_TOKEN=<your_access_token>
STRAVA_REFRESH_TOKEN=<your_refresh_token>
STRAVA_EXPIRES_AT=<timestamp>
```

## Usage

### List Activities

Fetch a page of activities:

```bash
poetry run python scripts/cli.py fetch-activities --per-page 30 --page 1

# Filter by date
poetry run python scripts/cli.py fetch-activities --after $(date -v-7d +%s)
```

### Fetch Stream Data

Fetch stream data for a single activity:

```bash
# Print all available streams to console (pretty-printed JSON)
poetry run python scripts/cli.py fetch-stream 123456789

# Save to a file
poetry run python scripts/cli.py fetch-stream 123456789 --output activity_data.json

# Fetch specific streams only
poetry run python scripts/cli.py fetch-stream 123456789 --keys "heartrate,watts,cadence"
```

**Available stream types:** `time`, `latlng`, `distance`, `altitude`, `velocity_smooth`, `heartrate`, `cadence`, `watts`, `temp`, `moving`, `grade_smooth`

### Backfill Activities

Download all activities to parquet files:

```bash
# Backfill all activities (uses 5 parallel workers by default)
poetry run python scripts/cli.py backfill-activities

# Backfill activities from 2024
poetry run python scripts/cli.py backfill-activities --after 1704067200 --before 1735689600

# Backfill recent activities (last 7 days)
poetry run python scripts/cli.py backfill-activities --after $(date -v-7d +%s)

# Use 10 parallel workers for faster downloads
poetry run python scripts/cli.py backfill-activities --max-workers 10

# Test with just 5 activities
poetry run python scripts/cli.py backfill-activities --max-activities 5
```

Activities are saved to:
- `data/activities/{activity_id}.parquet` - stream data per activity
- `data/metadata.parquet` - metadata for all activities

### Query Data

Show summary statistics:

```bash
poetry run python scripts/cli.py stats
```

Run custom SQL queries:

```bash
# Count activities by type
poetry run python scripts/cli.py query "SELECT type, COUNT(*) FROM metadata GROUP BY type"

# Get total distance for rides
poetry run python scripts/cli.py query "SELECT SUM(distance)/1000 as total_km FROM metadata WHERE type='Ride'"
```

## Technical Stack

- Python 3.11+
- Poetry for dependency management
- Pydantic v2 + pydantic-settings for configuration
- Click for CLI
- requests for HTTP
- pyarrow for Parquet files
- DuckDB for SQL queries
