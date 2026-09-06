# FLOOD-X — Real Data Upgrade Guide

> How to replace every `SYNTHETIC_PROTOTYPE` provider with real-world data.  
> The provider abstraction is specifically designed to make this a **drop-in replacement**.

---

## Architecture: Provider Abstraction

Every data source implements the same interface pattern:

```python
class BaseRainfallProvider(ABC):
    @abstractmethod
    async def get_current(self) -> RainfallObservation: ...
    @abstractmethod
    async def get_forecast(self, hours: int) -> List[RainfallObservation]: ...
```

To switch to real data: implement the interface, update `RAINFALL_PROVIDER=imd` in `.env`.

---

## 1. Rainfall → IMD API

**Current:** `SyntheticRainfallProvider` — simulation-driven intensity

**Target:** IMD (India Meteorological Department) real-time API

```python
# Create: backend/app/providers/imd_rainfall.py

import httpx
from app.schemas import RainfallObservation
from app.core.config import settings

class IMDRainfallProvider:
    BASE_URL = "https://api.imd.gov.in/api/v2"
    CHENNAI_STATION_ID = "43279"  # Chennai Airport AWS

    async def get_current(self) -> RainfallObservation:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.BASE_URL}/obs/aws/{self.CHENNAI_STATION_ID}/current",
                headers={"X-API-Key": settings.IMD_API_KEY},
                timeout=10.0,
            )
            r.raise_for_status()
            raw = r.json()
            return RainfallObservation(
                intensity_mm_hr=raw["rain_rate_mm_hr"],
                category=self._classify(raw["rain_rate_mm_hr"]),
                accumulated_mm=raw["accum_rain_mm"],
                timestamp=raw["obs_time"],
                data_source="IMD_LIVE",
                station_id=self.CHENNAI_STATION_ID,
            )
```

**Required:** IMD API key (apply at https://mausam.imd.gov.in)  
**Env var:** `IMD_API_KEY=your_key_here`  
**Config:** `RAINFALL_PROVIDER=imd`

---

## 2. Terrain / DEM → SRTM 30m

**Current:** Hardcoded elevation/slope values per catchment

**Target:** SRTM 30m Digital Elevation Model (public domain)

```bash
# 1. Download Chennai tile
# https://earthexplorer.usgs.gov/
# Tile: N12E080 (SRTM1, 30m resolution)
# Format: GeoTIFF

# 2. Clip to Chennai bbox
gdal_translate -projwin 80.0 13.2 80.4 12.8 \
    srtm_n12_e080.tif data/terrain/chennai_dem_30m.tif

# 3. Compute slope
gdaldem slope data/terrain/chennai_dem_30m.tif data/terrain/chennai_slope.tif
```

```python
# Create: backend/app/providers/file_terrain.py

import rasterio
import numpy as np

class FileTerrainProvider:
    def __init__(self):
        self._dem = rasterio.open("data/terrain/chennai_dem_30m.tif")
        self._slope = rasterio.open("data/terrain/chennai_slope.tif")

    async def get_catchment_terrain(self, lat, lon, radius_m=1000):
        # Sample DEM within catchment radius
        elev = self._sample_mean(self._dem, lat, lon, radius_m)
        slope = self._sample_mean(self._slope, lat, lon, radius_m)
        return TerrainData(elevation_m=elev, slope_pct=slope)
```

**Config:** `TERRAIN_PROVIDER=file`

---

## 3. Drainage Network → CMWSSB SCADA

**Current:** Synthetic 30-node network with computed utilization

**Target:** Chennai Metropolitan Water Supply and Sewerage Board real sensor data

```python
# Create: backend/app/providers/cmwssb_drainage.py

class CMWSSBDrainageProvider:
    SCADA_URL = "http://scada.cmwssb.gov.in/api/v1"

    async def get_network_status(self, intensity_mm_hr: float):
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.SCADA_URL}/drainage/status",
                headers={"Authorization": f"Bearer {settings.CMWSSB_TOKEN}"},
            )
            nodes = r.json()["nodes"]
            return DrainageNetworkStatus(
                nodes=[DrainageNode(**n) for n in nodes],
                timestamp=datetime.utcnow(),
                data_source="CMWSSB_LIVE",
            )
```

**Required:** CMWSSB data sharing agreement  
**Config:** `DRAINAGE_PROVIDER=cmwssb`

---

## 4. Road Network → OpenStreetMap (osmnx)

**Current:** 22 hardcoded road nodes with synthetic edges

**Target:** Full Chennai road network via osmnx (50,000+ nodes)

```python
# scripts/build_road_graph.py

import osmnx as ox
import networkx as nx
import pickle

# Download Chennai road network
G = ox.graph_from_place(
    "Chennai, India",
    network_type="drive",
    simplify=True,
)

# Add flood-susceptibility attribute to edges
# (requires spatial join with DEM data)
for u, v, data in G.edges(data=True):
    data["flood_weight"] = 1.0  # default — updated per-tick

# Save
with open("data/road_graph_chennai.pkl", "wb") as f:
    pickle.dump(G, f)

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
```

```python
# Update: backend/app/services/routing/graph.py

import pickle
G = pickle.load(open("data/road_graph_chennai.pkl", "rb"))
```

**Approximate:** 50,000 nodes, 120,000 edges for Chennai city limits

---

## 5. ML Model → Real Event Training

**Current:** XGBoost trained on 8000 synthetic simulation samples

**Target:** Retrain on real historical flood events

```python
# Collect real training data from:
# - IMD historical rainfall (2000–2025)
# - CMWSSB drainage sensor logs
# - Chennai Corporation flood reports
# - Satellite inundation maps (Sentinel-1 SAR)

# Then retrain with the same pipeline:
python scripts/train_models.py
# The training script is data-agnostic — just replace the generator
# with a real CSV loader in data_generator.py
```

**Key requirement:** At minimum 500 real flood events (flooded=1) for classifier training.

---

## 6. Deployment Checklist for Real Data

```
[ ] IMD API key obtained and tested
[ ] Chennai SRTM DEM downloaded and processed
[ ] CMWSSB data sharing MoU signed
[ ] osmnx road graph built and saved
[ ] Real historical flood labels collected (minimum 500 events)
[ ] ML model retrained on real data
[ ] All providers switched in .env
[ ] End-to-end validation: predicted vs observed flood extents
[ ] Performance benchmarked (API latency with real DB)
[ ] CORS locked to production domain
[ ] SECRET_KEY rotated to production value
```

---

## Estimated Integration Effort

| Component | Effort | Blocker |
|-----------|--------|---------|
| IMD Rainfall | 1 week | API key approval (2–4 weeks) |
| SRTM Terrain | 2 days | None (public data) |
| OSM Road Graph | 1 day | None (open data) |
| CMWSSB Drainage | 4 weeks | Data sharing agreement |
| Real ML training | 2 weeks | Real flood event labels |
| Full validation | 4 weeks | Real event comparison |

**Minimum viable real-data deployment:** ~3 months with IMD + OSM + SRTM only.
