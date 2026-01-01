from __future__ import annotations

from pathlib import Path

import duckdb


ACTIVITIES_DIR = Path("data/activities")
METADATA_FILE = Path("data/metadata.parquet")


def execute_query(sql: str) -> list[tuple]:
    """Execute a SQL query against the parquet files.

    Args:
        sql: SQL query string. Can reference:
             - 'metadata' for data/metadata.parquet
             - 'activities' for data/activities/*.parquet

    Returns:
        List of result tuples
    """
    conn = duckdb.connect(":memory:")

    # Register views for easier querying
    if METADATA_FILE.exists():
        conn.execute(f"CREATE VIEW metadata AS SELECT * FROM '{METADATA_FILE}'")

    if ACTIVITIES_DIR.exists():
        conn.execute(
            f"CREATE VIEW activities AS SELECT * FROM '{ACTIVITIES_DIR}/*.parquet'"
        )

    result = conn.execute(sql).fetchall()
    conn.close()

    return result


def get_summary_stats() -> dict[str, any]:
    """Get summary statistics about downloaded activities."""

    if not METADATA_FILE.exists():
        return {"error": "No metadata file found. Run backfill-activities first."}

    conn = duckdb.connect(":memory:")
    conn.execute(f"CREATE VIEW metadata AS SELECT * FROM '{METADATA_FILE}'")

    # Total activities
    total = conn.execute("SELECT COUNT(*) FROM metadata").fetchone()[0]

    # Activities by type
    by_type = conn.execute(
        """
        SELECT type, COUNT(*) as count
        FROM metadata
        GROUP BY type
        ORDER BY count DESC
    """
    ).fetchall()

    # Total distance and time
    totals = conn.execute(
        """
        SELECT
            SUM(distance) / 1000 as total_km,
            SUM(moving_time) / 3600 as total_hours,
            SUM(total_elevation_gain) as total_elevation_m
        FROM metadata
    """
    ).fetchone()

    # Date range
    date_range = conn.execute(
        """
        SELECT
            MIN(start_date) as first_activity,
            MAX(start_date) as last_activity
        FROM metadata
    """
    ).fetchone()

    # Activities per year
    by_year = conn.execute(
        """
        SELECT
            EXTRACT(year FROM start_date::TIMESTAMP) as year,
            COUNT(*) as count
        FROM metadata
        GROUP BY year
        ORDER BY year DESC
    """
    ).fetchall()

    # Activities per month (last 12 months)
    by_month = conn.execute(
        """
        SELECT
            STRFTIME(start_date::TIMESTAMP, '%Y-%m') as month,
            COUNT(*) as count
        FROM metadata
        WHERE start_date::TIMESTAMP >= CURRENT_DATE - INTERVAL 12 MONTHS
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """
    ).fetchall()

    conn.close()

    return {
        "total_activities": total,
        "by_type": by_type,
        "total_km": round(totals[0], 1) if totals[0] else 0,
        "total_hours": round(totals[1], 1) if totals[1] else 0,
        "total_elevation_m": round(totals[2], 1) if totals[2] else 0,
        "first_activity": date_range[0],
        "last_activity": date_range[1],
        "by_year": by_year,
        "by_month": by_month,
    }


def get_stream_coverage() -> dict[str, int]:
    """Check which activities have which stream types."""

    if not ACTIVITIES_DIR.exists():
        return {"error": "No activities directory found."}

    conn = duckdb.connect(":memory:")

    # Query all activity files and check which columns exist
    result = conn.execute(
        f"""
        SELECT
            COUNT(*) as total_files,
            COUNT(CASE WHEN heartrate IS NOT NULL THEN 1 END) as has_heartrate,
            COUNT(CASE WHEN watts IS NOT NULL THEN 1 END) as has_power,
            COUNT(CASE WHEN cadence IS NOT NULL THEN 1 END) as has_cadence,
            COUNT(CASE WHEN lat IS NOT NULL THEN 1 END) as has_gps,
            COUNT(CASE WHEN altitude IS NOT NULL THEN 1 END) as has_altitude
        FROM '{ACTIVITIES_DIR}/*.parquet'
    """
    ).fetchone()

    conn.close()

    return {
        "total_files": result[0],
        "has_heartrate": result[1],
        "has_power": result[2],
        "has_cadence": result[3],
        "has_gps": result[4],
        "has_altitude": result[5],
    }
