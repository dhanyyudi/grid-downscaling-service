# main.py
# Application entry point

"""
Grid Downscaling Service
========================
REST API for interpolating land values from 50m to 5m grids.

The service exposes two main feature groups:
1. Land Value queries - get interpolated values by coord, GID, or polygon
2. Grid utilities - convert between coords/GIDs, get geometries, polyfill, etc.

Run with:
    uvicorn main:app --reload --port 8000
"""

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import API_TITLE, API_VERSION
from services.interpolator import LandValueInterpolator
from routes import land_value, grid_utils
from geosquare_grid import GeosquareGrid


# Create the app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="Interpolates land values from 50m to 5m grids, and exposes grid utility functions.",
    docs_url="/docs"
)

# Allow frontend to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state - populated on startup
interpolator = None
grid = GeosquareGrid()


@app.on_event("startup")
async def startup():
    """Load the interpolator when the app starts."""
    global interpolator
    
    print("=" * 50)
    print(f"Starting {API_TITLE} v{API_VERSION}")
    print("=" * 50)
    
    start = time.time()
    interpolator = LandValueInterpolator()
    
    # Wire up the routes with dependencies
    land_value.set_dependencies(interpolator, grid)
    
    print(f"Ready in {time.time() - start:.1f}s")
    print("=" * 50)


# Mount the routers
app.include_router(land_value.router)
app.include_router(grid_utils.router)


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API overview."""
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "endpoints": {
            "land_value": [
                "GET /land-value?lat=&lon=",
                "GET /land-value/{gid}",
                "POST /land-value/polygon"
            ],
            "grid_utils": [
                "GET /grid/lonlat-to-gid",
                "GET /grid/gid-to-lonlat",
                "GET /grid/gid-to-bound",
                "GET /grid/gid-to-geometry",
                "POST /grid/polyfill",
                "GET /grid/children"
            ]
        }
    }


@app.get("/status", tags=["System"])
async def status():
    """Check if the service is ready."""
    return {
        "status": "ok" if interpolator else "starting",
        "interpolator_ready": interpolator is not None,
        "cells_loaded": len(interpolator.parent_values) if interpolator else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
