# slipstream

Cycling data analysis and ingestion tooling for Strava performance data.

> **Note**: This project is being developed with significant contributions from Claude (Anthropic's AI assistant). Much of the codebase architecture, refactoring, and tooling setup has been collaboratively designed and implemented with AI assistance.

## Goal

Analyze cycling performance data to detect fatigue patterns and improve FTP (Functional Threshold Power) and pacing strategy.

## Current Status

**Phase 0: Authentication & Data Ingestion**

The project currently supports:
- OAuth authentication with Strava API
- Fetching activity lists and detailed stream data (HR, power, cadence, altitude, GPS)
- Stateless credential management via environment variables

## Future Phases

- **Phase 1**: Historical data backfill and storage (Parquet files), incremental updates
- **Phase 2**: Batch analysis with Spark to identify fatigue patterns and pacing strategies
- **Phase 3**: Real-time stream processing with Flink for live workout guidance
- **Phase 4**: Enhanced analytics with sleep, nutrition, and training load context

## Technical Stack

- Python 3.11+
- Poetry for dependency management
- Pydantic v2 + pydantic-settings for configuration
- Click for CLI
- requests for HTTP

## Getting Started

### Installation

```bash
poetry install
```

### Authentication

1. Set your Strava OAuth client credentials:

```bash
export STRAVA_CLIENT_ID=<your_client_id>
export STRAVA_CLIENT_SECRET=<your_client_secret>
```

2. Start the OAuth authorization flow:

```bash
poetry run python scripts/cli.py auth-start
```

3. Visit the URL printed above, authorize the application, and copy the `code` from the redirect URL.

4. Exchange the code for access tokens:

```bash
poetry run python scripts/cli.py auth-exchange <code>
```

5. Copy the export commands from the output and run them to set your tokens:

```bash
export STRAVA_ACCESS_TOKEN=<your_access_token>
export STRAVA_REFRESH_TOKEN=<your_refresh_token>
export STRAVA_EXPIRES_AT=<timestamp>
```

Alternatively, add all variables to a `.env` file in the project root:

```
STRAVA_CLIENT_ID=<your_client_id>
STRAVA_CLIENT_SECRET=<your_client_secret>
STRAVA_ACCESS_TOKEN=<your_access_token>
STRAVA_REFRESH_TOKEN=<your_refresh_token>
STRAVA_EXPIRES_AT=<timestamp>
```

### Usage

Fetch a page of activities:

```bash
poetry run python scripts/cli.py fetch-activities --per-page 30 --page 1
```

Fetch streams for a single activity:

```bash
poetry run python scripts/cli.py fetch-stream 123456789
```
