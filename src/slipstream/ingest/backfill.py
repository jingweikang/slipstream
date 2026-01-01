from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from slipstream.ingest.strava import fetch_activity_streams, list_activities


logger = logging.getLogger(__name__)

ACTIVITIES_DIR = Path("data/activities")
METADATA_FILE = Path("data/metadata.parquet")
FAILURES_LOG = Path("data/failures.log")


def _ensure_data_dirs() -> None:
    """Create data directories if they don't exist."""
    ACTIVITIES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)


def _process_stream_data(streams: dict[str, Any]) -> pd.DataFrame:
    """Convert stream data to DataFrame with lat/lng split."""
    data = {}

    for stream_type, stream_info in streams.items():
        if stream_type == "latlng":
            latlng_data = stream_info["data"]
            data["lat"] = [point[0] if point else None for point in latlng_data]
            data["lng"] = [point[1] if point else None for point in latlng_data]
        else:
            data[stream_type] = stream_info["data"]

    return pd.DataFrame(data)


def _save_activity_streams(activity_id: int) -> bool:
    """Fetch and save stream data for a single activity.

    Returns:
        bool: True if successful, False if failed
    """
    output_file = ACTIVITIES_DIR / f"{activity_id}.parquet"

    if output_file.exists():
        logger.info(f"Activity {activity_id}: Already exists, skipping")
        return True

    try:
        streams = fetch_activity_streams(activity_id)

        if not streams:
            logger.warning(f"Activity {activity_id}: No stream data available")
            return False

        df = _process_stream_data(streams)
        df.to_parquet(output_file, index=False)

        logger.info(f"Activity {activity_id}: Saved {len(df)} data points")
        return True

    except requests.HTTPError as e:
        if e.response and e.response.status_code == 429:
            logger.error(f"Activity {activity_id}: Rate limited (429)")
            raise
        logger.error(f"Activity {activity_id}: HTTP error - {e}")
        return False
    except Exception as e:
        logger.error(f"Activity {activity_id}: Failed - {e}")
        return False


def _save_metadata(activities: list[dict[str, Any]]) -> None:
    """Save activity metadata to parquet file (append mode)."""
    if not activities:
        return

    new_df = pd.DataFrame(activities)

    if METADATA_FILE.exists():
        existing_df = pd.read_parquet(METADATA_FILE)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.drop_duplicates(subset=["id"], keep="last", inplace=True)
        combined_df.to_parquet(METADATA_FILE, index=False)
    else:
        new_df.to_parquet(METADATA_FILE, index=False)

    logger.info(f"Metadata: Saved {len(activities)} activities")


def backfill_activities(
    max_activities: int | None = None,
    before: int | None = None,
    after: int | None = None,
    max_workers: int = 5,
) -> None:
    """Backfill activities from Strava to parquet files.

    Args:
        max_activities: Optional limit on number of activities to process
        before: Epoch timestamp to filter activities before this time
        after: Epoch timestamp to filter activities after this time
        max_workers: Number of parallel threads for downloading (default: 5)
    """
    _ensure_data_dirs()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    page = 1
    total_processed = 0
    total_failed = 0
    failures = []

    logger.info("Starting activity backfill...")
    logger.info(f"Using {max_workers} parallel workers")
    if before:
        logger.info(f"Filtering activities before: {before}")
    if after:
        logger.info(f"Filtering activities after: {after}")

    while True:
        logger.info(f"Fetching page {page}...")

        try:
            activities = list_activities(
                per_page=200, page=page, before=before, after=after
            )
        except Exception as e:
            logger.error(f"Failed to fetch activities page {page}: {e}")
            break

        if not activities:
            logger.info("No more activities to process")
            break

        logger.info(f"Processing {len(activities)} activities from page {page}")

        _save_metadata(activities)

        activities_to_process = []
        for activity in activities:
            if (
                max_activities
                and total_processed + len(activities_to_process) >= max_activities
            ):
                break
            activities_to_process.append(activity["id"])

        if not activities_to_process:
            if max_activities:
                logger.info(f"Reached max activities limit ({max_activities})")
            break

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_activity = {
                executor.submit(_save_activity_streams, activity_id): activity_id
                for activity_id in activities_to_process
            }

            for future in as_completed(future_to_activity):
                activity_id = future_to_activity[future]
                try:
                    success = future.result()
                    if not success:
                        total_failed += 1
                        failures.append(activity_id)
                except Exception as e:
                    logger.error(f"Activity {activity_id}: Exception - {e}")
                    total_failed += 1
                    failures.append(activity_id)

                total_processed += 1

        if max_activities and total_processed >= max_activities:
            logger.info(f"Reached max activities limit ({max_activities})")
            break

        if len(activities) < 200:
            logger.info("Reached end of activities (last page)")
            break

        page += 1

        time.sleep(1)

    logger.info(
        f"Backfill complete: {total_processed} processed, {total_failed} failed"
    )
    _log_failures(failures)


def _log_failures(failures: list[int]) -> None:
    """Write failed activity IDs to failures log."""
    if not failures:
        return

    with open(FAILURES_LOG, "a") as f:
        for activity_id in failures:
            f.write(f"{activity_id}\n")

    logger.info(f"Logged {len(failures)} failures to {FAILURES_LOG}")
