import json
import click
from slipstream.ingest.auth import build_authorization_url, exchange_code_for_token
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
def fetch_activities_cmd(per_page: int, page: int):
    """Fetch and print a page of activities for the authorized user."""
    acts = list_activities(per_page=per_page, page=page)
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


if __name__ == "__main__":
    cli()
