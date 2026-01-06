# models.py
# Pydantic models for request/response validation

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# --- Land Value Models ---

class PointQuery(BaseModel):
    """Response for point-based land value queries."""
    gid: str
    level: int
    value: Optional[float]
    source: str  # 'original' or 'interpolated'
    lon: Optional[float] = None
    lat: Optional[float] = None


class PolygonRequest(BaseModel):
    """Request body for polygon queries."""
    coordinates: List[List[float]] = Field(
        ...,
        description="Polygon as [[lon, lat], ...]. Must have at least 4 pairs (closed ring).",
        example=[[106.8, -6.2], [106.82, -6.2], [106.82, -6.22], [106.8, -6.22], [106.8, -6.2]]
    )


class PolygonResult(BaseModel):
    """Response for polygon-based queries."""
    area_km2: float
    cell_count: int
    avg_value: Optional[float]


# --- Grid Utility Models ---

class PolyfillRequest(BaseModel):
    """Request body for polyfill operation."""
    coordinates: List[List[float]] = Field(
        ...,
        description="Polygon coordinates"
    )
    size: int = Field(
        50,
        description="Target cell size in meters. Valid: 1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000"
    )
    fullcover: bool = Field(
        True,
        description="If true, only return cells fully inside polygon"
    )


class GIDListResponse(BaseModel):
    """Response containing a list of GIDs."""
    count: int
    gids: List[str]
    truncated: bool = False  # True if list was cut off


# --- System Models ---

class ServiceStatus(BaseModel):
    """Service health/status response."""
    status: str
    interpolator_ready: bool
    cells_loaded: int
