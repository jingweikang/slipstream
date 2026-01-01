"""FastAPI web application for activity map visualization."""

from __future__ import annotations

from pathlib import Path

import duckdb
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from slipstream.analysis.query import METADATA_FILE
from slipstream.web.models import (
    ActivitiesResponse,
    ActivitySummary,
    FilterOptions,
)


app = FastAPI(title="Slipstream Map Viewer")

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Simple in-memory cache
_activity_cache: dict | None = None
_cache_timestamp: float | None = None
CACHE_TTL = 300  # 5 minutes


def _build_where_clause(
    type_filter: str | None = None,
    min_distance: float | None = None,
    max_distance: float | None = None,
    min_elevation: float | None = None,
    max_elevation: float | None = None,
) -> str:
    """Build WHERE clause for activity filtering."""
    conditions = ["map.summary_polyline != ''"]

    if type_filter:
        conditions.append(f"type = '{type_filter}'")
    if min_distance is not None:
        conditions.append(f"distance >= {min_distance}")
    if max_distance is not None:
        conditions.append(f"distance <= {max_distance}")
    if min_elevation is not None:
        conditions.append(f"total_elevation_gain >= {min_elevation}")
    if max_elevation is not None:
        conditions.append(f"total_elevation_gain <= {max_elevation}")

    return " AND ".join(conditions)


@app.get("/")
async def serve_frontend():
    """Serve the main HTML page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/activities", response_model=ActivitiesResponse)
async def get_activities(
    type: str | None = Query(None, description="Filter by activity type"),
    min_distance: float | None = Query(None, description="Minimum distance in meters"),
    max_distance: float | None = Query(None, description="Maximum distance in meters"),
    min_elevation: float | None = Query(
        None, description="Minimum elevation gain in meters"
    ),
    max_elevation: float | None = Query(
        None, description="Maximum elevation gain in meters"
    ),
):
    """Get all activities with GPS data, optionally filtered."""
    conn = duckdb.connect(":memory:")

    where_clause = _build_where_clause(
        type, min_distance, max_distance, min_elevation, max_elevation
    )

    query = f"""
        SELECT
            id, name, type, sport_type, distance, total_elevation_gain,
            start_date, start_latlng, end_latlng,
            map.summary_polyline as polyline,
            moving_time, average_speed
        FROM '{METADATA_FILE}'
        WHERE {where_clause}
        ORDER BY start_date DESC
    """

    results = conn.execute(query).fetchall()
    conn.close()

    activities = [
        ActivitySummary(
            id=row[0],
            name=row[1],
            type=row[2],
            sport_type=row[3],
            distance=row[4],
            total_elevation_gain=row[5],
            start_date=row[6],
            start_latlng=list(row[7]) if row[7] else None,
            end_latlng=list(row[8]) if row[8] else None,
            polyline=row[9],
            moving_time=row[10],
            average_speed=row[11],
        )
        for row in results
    ]

    return ActivitiesResponse(activities=activities, count=len(activities))


@app.get("/api/filter-options", response_model=FilterOptions)
async def get_filter_options():
    """Get available filter options."""
    conn = duckdb.connect(":memory:")

    # Get unique types (only for activities with GPS)
    types = conn.execute(
        f"""
        SELECT DISTINCT type
        FROM '{METADATA_FILE}'
        WHERE map.summary_polyline != ''
        ORDER BY type
    """
    ).fetchall()

    # Get distance range
    distance_range = conn.execute(
        f"""
        SELECT MIN(distance), MAX(distance)
        FROM '{METADATA_FILE}'
        WHERE map.summary_polyline != ''
    """
    ).fetchone()

    # Get elevation range
    elevation_range = conn.execute(
        f"""
        SELECT MIN(total_elevation_gain), MAX(total_elevation_gain)
        FROM '{METADATA_FILE}'
        WHERE map.summary_polyline != '' AND total_elevation_gain IS NOT NULL
    """
    ).fetchone()

    conn.close()

    return FilterOptions(
        types=[t[0] for t in types],
        distance_range={"min": distance_range[0] or 0, "max": distance_range[1] or 0},
        elevation_range={
            "min": elevation_range[0] or 0,
            "max": elevation_range[1] or 0,
        },
    )
