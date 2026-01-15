import asyncio
import json

import click


@click.group()
def cli():
    """Slipstream CLI (single-user)."""
    pass


@cli.command(name="auth-start")
def auth_start():
    """Print the authorization URL to visit in a browser."""
    from slipstream.ingest.auth import build_authorization_url
    from slipstream.settings import settings

    url = build_authorization_url(
        str(settings.STRAVA_CLIENT_ID),
        settings.STRAVA_REDIRECT_URI,
    )
    click.echo("Visit this URL to authorize the application:")
    click.echo(url)


@cli.command(name="auth-exchange")
@click.argument("code")
def auth_exchange(code: str):
    """Exchange a code (from the redirect) for tokens.

    This will print the tokens that you need to set as environment variables.
    """
    from slipstream.ingest.auth import exchange_code_for_token
    from slipstream.settings import settings

    resp = exchange_code_for_token(
        code,
        str(settings.STRAVA_CLIENT_ID),
        settings.STRAVA_CLIENT_SECRET,
    )

    click.echo("\nAuthentication successful!")
    click.echo("Set these environment variables to use the API:\n")
    click.echo(f"export STRAVA_ACCESS_TOKEN={resp['access_token']}")
    click.echo(f"export STRAVA_REFRESH_TOKEN={resp['refresh_token']}")
    click.echo(f"export STRAVA_EXPIRES_AT={resp['expires_at']}")
    click.echo("\nOr add them to your .env file:")
    click.echo(f"STRAVA_ACCESS_TOKEN={resp['access_token']}")
    click.echo(f"STRAVA_REFRESH_TOKEN={resp['refresh_token']}")
    click.echo(f"STRAVA_EXPIRES_AT={resp['expires_at']}")


@cli.command(name="fetch-activities")
@click.option("--per-page", default=30, help="Activities per page")
@click.option("--page", default=1, help="Page number")
@click.option(
    "--before", type=int, help="Epoch timestamp: filter activities before this time"
)
@click.option(
    "--after", type=int, help="Epoch timestamp: filter activities after this time"
)
def fetch_activities_cmd(
    per_page: int, page: int, before: int | None, after: int | None
):
    """Fetch and print a page of activities for the authorized user."""
    from slipstream.ingest.strava import list_activities

    acts = list_activities(per_page=per_page, page=page, before=before, after=after)
    click.echo(f"Found activities: {len(acts) if isinstance(acts, list) else 0}")
    for a in acts:
        click.echo(
            f"{a['id']}: {a.get('name')} ({a.get('type')}) {a.get('start_date')}"
        )


@cli.command(name="fetch-stream")
@click.argument("activity_id", type=int)
@click.option("--output", "-o", help="Output file path (JSON)")
@click.option("--pretty/--no-pretty", default=True, help="Pretty print JSON")
@click.option(
    "--keys",
    help="Comma-separated stream types (e.g., 'heartrate,watts,cadence'). Defaults to all available streams.",
)
def fetch_stream(activity_id: int, output: str, pretty: bool, keys: str):
    """Fetch streams for a single activity and print or save the data."""
    from slipstream.ingest.strava import fetch_activity_streams

    if keys:
        streams = fetch_activity_streams(activity_id, keys=keys)
    else:
        streams = fetch_activity_streams(activity_id)

    if output:
        with open(output, "w") as f:
            json.dump(streams, f, indent=2 if pretty else None)
        click.echo(f"Saved stream data to {output}")
    else:
        if pretty:
            click.echo(json.dumps(streams, indent=2))
        else:
            click.echo(json.dumps(streams))


@cli.command(name="backfill-activities")
@click.option(
    "--max-activities",
    type=int,
    help="Maximum number of activities to process (useful for testing)",
)
@click.option(
    "--before",
    type=int,
    help="Epoch timestamp: only backfill activities before this time",
)
@click.option(
    "--after",
    type=int,
    help="Epoch timestamp: only backfill activities after this time (useful for incremental updates)",
)
@click.option(
    "--max-workers",
    type=int,
    default=5,
    help="Number of parallel download threads (default: 5)",
)
def backfill_activities_cmd(
    max_activities: int | None,
    before: int | None,
    after: int | None,
    max_workers: int,
):
    """Backfill activities from Strava to parquet files.

    This command will:
    - Fetch activities using pagination (with optional before/after filters)
    - Download stream data for each activity in parallel
    - Save streams as individual parquet files in data/activities/
    - Save activity metadata to data/metadata.parquet
    - Skip activities that already exist locally
    - Log failures to data/failures.log

    Examples:

    \b
    # Backfill all activities
    poetry run python scripts/cli.py backfill-activities

    \b
    # Backfill only recent activities (last 7 days)
    poetry run python scripts/cli.py backfill-activities --after $(date -v-7d +%s)

    \b
    # Test with just 5 activities
    poetry run python scripts/cli.py backfill-activities --max-activities 5

    \b
    # Use 10 parallel workers for faster downloads
    poetry run python scripts/cli.py backfill-activities --max-workers 10
    """
    from slipstream.ingest.backfill import backfill_activities

    backfill_activities(
        max_activities=max_activities,
        before=before,
        after=after,
        max_workers=max_workers,
    )


@cli.command(name="query")
@click.argument("sql")
def query_cmd(sql: str):
    """Execute a SQL query against parquet files.

    You can reference 'metadata' and 'activities' tables in your queries.

    Examples:

    \b
    # Count activities by type
    poetry run python scripts/cli.py query "SELECT type, COUNT(*) FROM metadata GROUP BY type"

    \b
    # Get activities with power data
    poetry run python scripts/cli.py query "SELECT COUNT(DISTINCT filename) FROM 'data/activities/*.parquet' WHERE watts IS NOT NULL"
    """
    from slipstream.analysis.query import execute_query

    try:
        results = execute_query(sql)

        if not results:
            click.echo("No results")
            return

        for row in results:
            click.echo("\t".join(str(x) for x in row))

    except Exception as e:
        click.echo(f"Error executing query: {e}", err=True)


@cli.command(name="stats")
def stats_cmd():
    """Show summary statistics about downloaded activities."""
    from slipstream.analysis.query import get_summary_stats

    stats = get_summary_stats()

    if "error" in stats:
        click.echo(stats["error"], err=True)
        return

    click.echo("=" * 60)
    click.echo("ACTIVITY SUMMARY STATISTICS")
    click.echo("=" * 60)
    click.echo()

    click.echo(f"Total Activities: {stats['total_activities']}")
    click.echo(f"Date Range: {stats['first_activity']} to {stats['last_activity']}")
    click.echo()

    click.echo(f"Total Distance: {stats['total_km']:,.1f} km")
    click.echo(f"Total Time: {stats['total_hours']:,.1f} hours")
    click.echo(f"Total Elevation: {stats['total_elevation_m']:,.1f} m")
    click.echo()

    click.echo("Activities by Type:")
    for activity_type, count in stats["by_type"]:
        click.echo(f"  {activity_type}: {count}")
    click.echo()

    if stats["by_year"]:
        click.echo("Activities by Year:")
        for year, count in stats["by_year"]:
            click.echo(f"  {int(year)}: {count}")
        click.echo()

    if stats["by_month"]:
        click.echo("Recent Months (last 12):")
        for month, count in stats["by_month"]:
            click.echo(f"  {month}: {count}")


@cli.command(name="web")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
def web_cmd(host: str, port: int):
    """Start the web map viewer.

    This command starts a web server that serves an interactive map
    of your activities with clustering and filtering capabilities.

    Example:

    \b
    # Start the web server (default: http://127.0.0.1:8080)
    poetry run python scripts/cli.py web

    \b
    # Start on a different port
    poetry run python scripts/cli.py web --port 9000
    """
    import uvicorn
    from slipstream.web.app import app

    click.echo(f"Starting web server at http://{host}:{port}")
    click.echo("Press Ctrl+C to stop")

    uvicorn.run(app, host=host, port=port)


@cli.command(name="garmin-hr-monitor")
@click.option(
    "--output-dir",
    type=click.Path(),
    default="data/garmin",
    help="Directory to save Parquet files",
)
@click.option(
    "--no-record",
    is_flag=True,
    help="Don't save data to file, only display real-time",
)
@click.option(
    "--scan-timeout",
    type=float,
    default=10.0,
    help="How long to scan for devices in seconds",
)
def garmin_hr_monitor_cmd(output_dir: str, no_record: bool, scan_timeout: float):
    """Monitor heart rate from Garmin device via Bluetooth.

    This command will:
    - Scan for available Garmin devices
    - Let you select a device
    - Connect and start monitoring heart rate
    - Display real-time HR data in the terminal
    - Record data to Parquet file (unless --no-record is specified)

    Requirements:
    - Garmin watch must be in pairing/broadcast mode
    - Bluetooth must be enabled on your Mac
    - Watch should not be connected to other devices

    Example:

    \b
    # Start monitoring (with recording)
    poetry run python scripts/cli.py garmin-hr-monitor

    \b
    # Monitor without recording
    poetry run python scripts/cli.py garmin-hr-monitor --no-record

    \b
    # Custom output directory and longer scan time
    poetry run python scripts/cli.py garmin-hr-monitor --output-dir data/hr --scan-timeout 15
    """
    from pathlib import Path

    from slipstream.garmin.ble_scanner import GarminDeviceScanner
    from slipstream.garmin.display import HeartRateDisplay
    from slipstream.garmin.hr_monitor import HeartRateData, HeartRateMonitor
    from slipstream.garmin.recorder import HeartRateRecorder

    async def monitor():
        scanner = GarminDeviceScanner()
        device = await scanner.scan_and_select()

        if device is None:
            click.echo("No device selected. Exiting.")
            return

        monitor = HeartRateMonitor(device)
        display = HeartRateDisplay()

        recorder = None
        if not no_record:
            recorder = HeartRateRecorder(Path(output_dir))

        try:
            connected = await monitor.connect()
            if not connected:
                click.echo("Failed to connect. Exiting.")
                return

            display.start_session()
            if recorder:
                recorder.start_session()

            def handle_data(data: HeartRateData):
                display.display(data)
                if recorder:
                    recorder.record(data)

            started = await monitor.start_monitoring(handle_data)
            if not started:
                click.echo("Failed to start monitoring. Exiting.")
                return

            click.echo("\nMonitoring... Press Ctrl+C to stop\n")

            # Keep running until interrupted
            try:
                while monitor.is_monitoring:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                click.echo("\n\nStopping monitoring...")

        finally:
            await monitor.stop_monitoring()
            await monitor.disconnect()

            display.print_summary()

            if recorder:
                recorder.save()

    # Run the async function
    asyncio.run(monitor())


if __name__ == "__main__":
    cli()
