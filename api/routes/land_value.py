# routes/land_value.py
# Endpoints for land value queries

from fastapi import APIRouter, HTTPException, Query
from shapely.geometry import Polygon
from shapely.ops import transform
import pyproj

from models import PolygonRequest, PolygonResult
from services.interpolator import LandValueInterpolator
from geosquare_grid import GeosquareGrid

router = APIRouter(prefix="/land-value", tags=["Land Value"])

# These get set by main.py on startup
interpolator: LandValueInterpolator = None
grid: GeosquareGrid = None


def set_dependencies(interp: LandValueInterpolator, g: GeosquareGrid):
    """Called by main.py to inject dependencies."""
    global interpolator, grid
    interpolator = interp
    grid = g


def _calc_area_km2(coords) -> float:
    """Project polygon to UTM and compute area in km²."""
    poly = Polygon(coords)
    # UTM zone 48S covers Jakarta
    proj = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32748", always_xy=True).transform
    projected = transform(proj, poly)
    return projected.area / 1_000_000


@router.get("")
async def by_coordinates(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    """
    Get interpolated land value at a coordinate.
    
    This converts the point to a 5m grid cell (Level 14) and 
    interpolates the value from nearby 50m cells using IDW.
    """
    if interpolator is None:
        raise HTTPException(503, "Service starting up, try again shortly")
    
    result = interpolator.get_value_at_coord(lon, lat)
    
    if "error" in result:
        raise HTTPException(400, result)
    
    return result


@router.get("/{gid}")
async def by_gid(gid: str):
    """
    Get land value for a specific grid cell.
    
    - 12-char GID: returns the original 50m cell value
    - 14-char GID: returns interpolated 5m cell value
    """
    if interpolator is None:
        raise HTTPException(503, "Service starting up")
    
    if len(gid) not in (12, 14):
        raise HTTPException(400, f"GID must be 12 or 14 characters, got {len(gid)}")
    
    result = interpolator.get_value_at_gid(gid)
    
    if "error" in result:
        raise HTTPException(400, result)
    
    return result


@router.post("/polygon", response_model=PolygonResult)
async def by_polygon(req: PolygonRequest):
    """
    Get aggregated land value stats for a polygon area.
    
    Uses polyfill to find all 50m cells that intersect with the polygon,
    then computes the average value.
    """
    if interpolator is None:
        raise HTTPException(503, "Service starting up")
    
    coords = req.coordinates
    if len(coords) < 4:
        raise HTTPException(400, "Polygon needs at least 4 coordinate pairs")
    
    try:
        area = _calc_area_km2(coords)
    except Exception as e:
        raise HTTPException(400, f"Invalid polygon geometry: {e}")
    
    # Use polyfill to get cells inside polygon
    poly = Polygon(coords)
    try:
        gids = grid.polyfill(poly, size=50, fullcover=False)
    except Exception as e:
        raise HTTPException(400, f"Polyfill failed: {e}")
    
    # Collect values from the cells we have data for
    values = []
    for gid in gids:
        if gid in interpolator.parent_values:
            values.append(interpolator.parent_values[gid])
    
    avg = round(sum(values) / len(values), 4) if values else None
    
    return PolygonResult(
        area_km2=round(area, 4),
        cell_count=len(values),
        avg_value=avg
    )
