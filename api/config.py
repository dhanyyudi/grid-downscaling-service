# config.py
# App configuration and constants

import os

# Data paths - can be overridden via environment variables
DATA_PATH = os.getenv("PARQUET_PATH", "gsq_material_dtengineer.parquet")

# IDW interpolation parameters
IDW_POWER = 2.0  # Standard inverse square weighting
IDW_NEIGHBORS = 9  # 8 surrounding cells + center

# Grid level to cell size mapping (meters)
# This comes from the geosquare-grid library
SIZE_TO_LEVEL = {
    10000000: 1,
    5000000: 2,
    1000000: 3,
    500000: 4,
    100000: 5,
    50000: 6,
    10000: 7,
    5000: 8,
    1000: 9,
    500: 10,
    100: 11,
    50: 12,  # Source data resolution
    10: 13,
    5: 14,   # Target resolution
    1: 15
}

# API metadata
API_TITLE = "Grid Downscaling Service"
API_VERSION = "1.0.0"
