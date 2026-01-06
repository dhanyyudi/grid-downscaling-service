# services/interpolator.py
# Core interpolation engine using IDW with R-tree spatial indexing

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Dict
from rtree import index
import time

from geosquare_grid import GeosquareGrid
from config import DATA_PATH, IDW_POWER, IDW_NEIGHBORS


class LandValueInterpolator:
    """
    Interpolates 50m grid values down to 5m resolution using IDW.
    
    The idea is simple: for any point, find the nearby 50m cells and
    compute a weighted average where closer cells have more influence.
    R-tree makes the neighbor lookup fast (O(log n) instead of O(n)).
    """
    
    def __init__(self, data_path: str = None):
        self.grid = GeosquareGrid()
        self.power = IDW_POWER
        self.k = IDW_NEIGHBORS
        
        path = data_path or DATA_PATH
        print(f"Loading data from {path}...")
        
        start = time.time()
        df = pd.read_parquet(path)
        print(f"  Loaded {len(df):,} rows in {time.time() - start:.2f}s")
        
        # We'll store values and centroids for each valid cell
        self.parent_values: Dict[str, float] = {}
        self.parent_centroids: Dict[str, Tuple[float, float]] = {}
        self.idx_to_gid: Dict[int, str] = {}
        
        # Track bounds from actual data
        min_lon, max_lon = float('inf'), float('-inf')
        min_lat, max_lat = float('inf'), float('-inf')
        
        # Build spatial index for fast neighbor queries
        print("Building spatial index...")
        start = time.time()
        self.rtree = index.Index()
        
        idx = 0
        for _, row in df.iterrows():
            gid = row['gid']
            val = row['value']
            
            # Skip cells with no data - can't interpolate from nothing
            if pd.isna(val):
                continue
            
            self.parent_values[gid] = float(val)
            
            # Calculate cell center from bounds
            bounds = self.grid.gid_to_bound(gid)
            cx = (bounds[0] + bounds[2]) / 2
            cy = (bounds[1] + bounds[3]) / 2
            self.parent_centroids[gid] = (cx, cy)
            
            # Update coverage bounds from data
            min_lon = min(min_lon, bounds[0])
            max_lon = max(max_lon, bounds[2])
            min_lat = min(min_lat, bounds[1])
            max_lat = max(max_lat, bounds[3])
            
            # Insert into R-tree (point stored as degenerate box)
            self.rtree.insert(idx, (cx, cy, cx, cy))
            self.idx_to_gid[idx] = gid
            idx += 1
        
        # Store computed bounds (derived from data, not hardcoded)
        self.coverage_bounds = {
            "min_lon": min_lon,
            "max_lon": max_lon,
            "min_lat": min_lat,
            "max_lat": max_lat
        }
        
        print(f"  Indexed {len(self.parent_values):,} cells in {time.time() - start:.2f}s")
        print(f"  Coverage: lon [{min_lon:.4f}, {max_lon:.4f}], lat [{min_lat:.4f}, {max_lat:.4f}]")
    
    def _haversine(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Great-circle distance in meters. Good enough for nearby points."""
        R = 6371000
        lat1_r, lat2_r = np.radians(lat1), np.radians(lat2)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon/2)**2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    def _find_neighbors(self, lon: float, lat: float) -> List[Tuple[str, float, float]]:
        """Find k nearest cells using R-tree. Returns [(gid, value, distance), ...]"""
        indices = list(self.rtree.nearest((lon, lat, lon, lat), self.k))
        
        result = []
        for idx in indices:
            gid = self.idx_to_gid[idx]
            val = self.parent_values[gid]
            cx, cy = self.parent_centroids[gid]
            dist = self._haversine(lon, lat, cx, cy)
            result.append((gid, val, dist))
        
        return sorted(result, key=lambda x: x[2])
    
    def interpolate(self, lon: float, lat: float) -> Optional[float]:
        """
        Compute IDW interpolated value at a point.
        
        If the point is basically on top of a known cell (< 1m), 
        just return that cell's value directly.
        """
        neighbors = self._find_neighbors(lon, lat)
        if not neighbors:
            return None
        
        # Direct hit - no need to interpolate
        if neighbors[0][2] < 1.0:
            return neighbors[0][1]
        
        # IDW: weighted average where weight = 1/distance^power
        total_w = 0.0
        weighted_sum = 0.0
        for gid, val, dist in neighbors:
            w = 1.0 / (dist ** self.power)
            weighted_sum += w * val
            total_w += w
        
        return round(weighted_sum / total_w, 4)
    
    def is_within_coverage(self, lon: float, lat: float) -> bool:
        """Check if coordinate is within data coverage area."""
        b = self.coverage_bounds
        return (b["min_lon"] <= lon <= b["max_lon"] and 
                b["min_lat"] <= lat <= b["max_lat"])
    
    def get_value_at_coord(self, lon: float, lat: float) -> dict:
        """Query by coordinate. Handles bounds checking."""
        if not self.is_within_coverage(lon, lat):
            return {"error": "Outside coverage area"}
        
        gid = self.grid.lonlat_to_gid(lon, lat, level=14)
        value = self.interpolate(lon, lat)
        
        return {
            "gid": gid,
            "level": 14,
            "lon": lon,
            "lat": lat,
            "value": value,
            "source": "interpolated"
        }
    
    def get_value_at_gid(self, gid: str) -> dict:
        """Query by GID. Level 12 returns original, Level 14 interpolates."""
        level = len(gid)
        
        if level == 12:
            # Direct lookup
            val = self.parent_values.get(gid)
            return {
                "gid": gid,
                "level": 12,
                "value": val,
                "source": "original"
            }
        elif level == 14:
            # Calculate center and interpolate
            bounds = self.grid.gid_to_bound(gid)
            cx = (bounds[0] + bounds[2]) / 2
            cy = (bounds[1] + bounds[3]) / 2
            val = self.interpolate(cx, cy)
            return {
                "gid": gid,
                "level": 14,
                "value": val,
                "source": "interpolated"
            }
        else:
            return {"error": f"Unsupported GID level: {level}. Use 12 or 14."}
