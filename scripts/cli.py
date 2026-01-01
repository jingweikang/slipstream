import json

import click
from slipstream.analysis.query import execute_query, get_summary_stats
from slipstream.ingest.auth import build_authorization_url, exchange_code_for_token
from slipstream.ingest.backfill import backfill_activities
from slipstream.ingest.strava import fetch_activity_streams, list_activities
from slipstream.settings import settings


@click.group()
def cli():
    """Slipstream CLI (single-user)."""
    pass


@cli.command(name="auth-start")
def auth_start():
    """Print the authorization URL to visit in a browser."""
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


if __name__ == "__main__":
    cli()
