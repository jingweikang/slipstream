"""Pydantic models for web API responses."""

from pydantic import BaseModel


class ActivitySummary(BaseModel):
    """Summary information for a single activity."""

    id: int
    name: str
    type: str
    sport_type: str
    distance: float
    total_elevation_gain: float | None
    start_date: str
    start_latlng: list[float] | None
    end_latlng: list[float] | None
    polyline: str
    moving_time: int | None
    average_speed: float | None


class ActivitiesResponse(BaseModel):
    """Response containing a list of activities."""

    activities: list[ActivitySummary]
    count: int


class FilterOptions(BaseModel):
    """Available filter options for activities."""

    types: list[str]
    distance_range: dict[str, float]
    elevation_range: dict[str, float]
