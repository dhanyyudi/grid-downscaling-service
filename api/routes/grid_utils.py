# routes/grid_utils.py
# Endpoints that expose the geosquare-grid library functionality

from fastapi import APIRouter, HTTPException, Query
from shapely.geometry import Polygon, mapping

from models import PolyfillRequest, GIDListResponse
from config import SIZE_TO_LEVEL
from geosquare_grid import GeosquareGrid

router = APIRouter(prefix="/grid", tags=["Grid Utilities"])

grid = GeosquareGrid()


@router.get("/lonlat-to-gid")
async def lonlat_to_gid(
    lon: float = Query(..., ge=-180, le=180),
    lat: float = Query(..., ge=-90, le=90),
    level: int = Query(12, ge=1, le=15)
):
    """
    Convert lon/lat coordinates to a grid ID at the specified level.
    
    Level controls the cell size (higher = finer):
    - Level 12: ~50m
    - Level 14: ~5m
    """
    try:
        gid = grid.lonlat_to_gid(lon, lat, level)
        return {"gid": gid, "level": level}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/gid-to-lonlat")
async def gid_to_lonlat(gid: str = Query(..., min_length=1, max_length=15)):
    """
    Get the lower-left corner coordinates of a grid cell.
    """
    try:
        lon, lat = grid.gid_to_lonlat(gid)
        return {"gid": gid, "lon": lon, "lat": lat}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/gid-to-bound")
async def gid_to_bound(gid: str = Query(..., min_length=1, max_length=15)):
    """
    Get the bounding box of a grid cell.
    
    Returns min/max lon/lat values.
    """
    try:
        b = grid.gid_to_bound(gid)
        return {
            "gid": gid,
            "min_lon": b[0], "min_lat": b[1],
            "max_lon": b[2], "max_lat": b[3]
        }
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/gid-to-geometry")
async def gid_to_geometry(gid: str = Query(..., min_length=1, max_length=15)):
    """
    Get the geometry of a grid cell as GeoJSON.
    
    Useful for visualization or spatial operations.
    """
    try:
        geom = grid.gid_to_geometry(gid)
        return {"gid": gid, "geometry": mapping(geom)}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/polyfill", response_model=GIDListResponse)
async def polyfill(req: PolyfillRequest):
    """
    Find all grid cells that cover a polygon.
    
    The 'size' parameter determines cell resolution (in meters).
    Set 'fullcover=false' to include cells that only partially overlap.
    
    Note: Response is capped at 1000 GIDs to avoid huge payloads.
    """
    if req.size not in SIZE_TO_LEVEL:
        raise HTTPException(400, f"Invalid size. Choose from: {list(SIZE_TO_LEVEL.keys())}")
    
    try:
        poly = Polygon(req.coordinates)
        gids = grid.polyfill(poly, size=req.size, fullcover=req.fullcover)
        
        # Cap the response to avoid memory issues
        truncated = len(gids) > 1000
        return GIDListResponse(
            count=len(gids),
            gids=gids[:1000],
            truncated=truncated
        )
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/children")
async def get_children(
    gid: str = Query(..., min_length=1, max_length=14),
    size: int = Query(5)
):
    """
    Get all child cells of a parent cell at a target size.
    
    Example: Get all 5m cells (Level 14) within a 50m cell (Level 12).
    """
    if size not in SIZE_TO_LEVEL:
        raise HTTPException(400, f"Invalid size. Choose from: {list(SIZE_TO_LEVEL.keys())}")
    
    target_level = SIZE_TO_LEVEL[size]
    if target_level <= len(gid):
        raise HTTPException(400, f"Target size must be finer than parent cell")
    
    try:
        children = grid.parrent_to_allchildren(gid, size)
        truncated = len(children) > 1000
        return {
            "parent": gid,
            "target_size": size,
            "count": len(children),
            "children": children[:1000],
            "truncated": truncated
        }
    except Exception as e:
        raise HTTPException(400, str(e))
