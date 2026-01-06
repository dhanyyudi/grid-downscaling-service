# Grid Downscaling Service

> **Note:** This project was developed as part of the Geosquare Data Engineer Challenge. The dataset used is provided specifically for this challenge and is not included in the repository.

Interpolates land values from 50m grid cells to 5m resolution using Inverse Distance Weighting (IDW).

## Overview

This service takes the 50m resolution land value dataset and provides on-demand downscaling to 5m resolution. It also exposes grid utility functions from the geosquare-grid library.

```
┌─────────────────┐         ┌─────────────────┐
│   Streamlit UI  │────────▶│   FastAPI       │
│   Port 8502     │         │   Port 8000     │
└─────────────────┘         └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Interpolator   │
                            │  (IDW + R-tree) │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Parquet Data   │
                            └─────────────────┘
```

## Project Structure

```
grid-downscaling-service/
├── api/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── routes/
│   │   ├── land_value.py    # /land-value endpoints
│   │   └── grid_utils.py    # /grid/* endpoints
│   ├── services/
│   │   └── interpolator.py  # IDW interpolation engine
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── streamlit_app.py
│   └── Dockerfile
├── data/
│   └── (parquet file - not included)
├── docker-compose.yml
└── README.md
```

## Prerequisites

**geosquare-grid library** (provided separately as part of the challenge):
```bash
pip install ./geosquare-grid
```

## Quick Start

### Run Locally

```bash
cd api

# Install deps
pip install -r requirements.txt
pip install /path/to/geosquare-grid

# Start API
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API docs.

### Run Frontend (optional)

```bash
cd frontend
pip install streamlit folium streamlit-folium requests
streamlit run streamlit_app.py --server.port 8502
```

## Docker Deployment

```bash
docker-compose up --build -d
```

Access:
- API: http://localhost:8000/docs
- Frontend: http://localhost:8502

## API Endpoints

### Land Value
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/land-value?lat=&lon=` | Interpolated value at coordinate |
| GET | `/land-value/{gid}` | Value by Grid ID |
| POST | `/land-value/polygon` | Aggregate for polygon area |

### Grid Utilities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/grid/lonlat-to-gid` | Coordinates → GID |
| GET | `/grid/gid-to-lonlat` | GID → Coordinates |
| GET | `/grid/gid-to-bound` | GID → Bounding box |
| GET | `/grid/gid-to-geometry` | GID → GeoJSON |
| POST | `/grid/polyfill` | Polygon → All GIDs |
| GET | `/grid/children` | Parent → Child GIDs |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API overview |
| GET | `/status` | Service status |

## Technical Notes

- **Interpolation**: IDW with power=2 and k=9 neighbors
- **Spatial Index**: R-tree for O(log n) neighbor lookups
- **Source Data**: Level 12 (~50m cells)
- **Target Data**: Level 14 (~5m cells)
- **Coverage Bounds**: Computed dynamically from data at startup
