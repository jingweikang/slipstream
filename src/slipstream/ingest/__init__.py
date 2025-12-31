"""Ingestion helpers for Strava and other sources.

This package-level module re-exports the primary helpers consumers
should import from `slipstream.ingest`.
"""

from .strava import fetch_activity_streams, list_activities

__all__ = ["list_activities", "fetch_activity_streams"]
