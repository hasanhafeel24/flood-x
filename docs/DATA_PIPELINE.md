# FLOOD-X — Data Pipeline

> Documents how data flows from raw inputs through processing to predictions.  
> All data in prototype is `SYNTHETIC_PROTOTYPE` — labelled on every stage.

---

## Pipeline Overview

```
Raw Inputs                Processing Layers              Outputs
──────────                ─────────────────              ───────
IMD Rainfall  ──────┐
CMWSSB SCADA  ──────┤   SCS-CN Hydrology               Nowcast (9 horizons)
SRTM DEM      ──────┤   ────────────────                Flood Clock
OSM Roads     ──────┤   Runoff → Peak Flow              Risk Score
                    │   Time of Concentration           Safe Route
                    ↓                                   Alerts
               Drainage Network                         Decisions
               ───────────────
               30-node utilization
               Surcharge detection
               Bottleneck graph
                    │
                    ↓
               ML Predictor (XGBoost)
               ─────────────────────
               14 features → probability
               Depth regressor
                    │
                    ↓
               Nowcast Engine
               ─────────────
               9 time horizons
               Confidence decay
               Flood Clock
                    │
                    ↓
               Risk Engine → Alerts → Decisions → WebSocket → Frontend
```

---

## Data Sources (Current Prototype)

### 1. Rainfall — `SyntheticRainfallProvider`

**File:** `backend/app/providers/synthetic_rainfall.py`

```
Synthetic data source  →  IMD intensity categories
                          (Light: <2.5, Moderate: 2.5–64.4,
                           Heavy: 64.5–115.5, Extreme: >115.5 mm/hr)
```

The simulation engine drives `current_intensity`, which the provider reads on each request.

**Real replacement path:**
```python
# providers/imd_rainfall.py
class IMDRainfallProvider:
    async def get_current(self) -> RainfallObservation:
        resp = await httpx.get(
            "https://api.imd.gov.in/rainfall/current",
            headers={"X-API-Key": settings.IMD_API_KEY}
        )
        return RainfallObservation(**resp.json())
```

---

### 2. Terrain / DEM — `SyntheticTerrainProvider`

**File:** `backend/app/providers/synthetic_terrain.py`

Each of the 12 catchments has hardcoded:
- `elevation_m` — approximate mean elevation above MSL (Chennai is largely 0–6m)
- `slope_pct` — 0.5–3% (flat coastal plain)
- `susceptibility` — weighted composite [0.0–1.0]

**Real replacement path:**
```bash
# SRTM 30m DEM — free, public domain
# Download: https://earthexplorer.usgs.gov/
# Process: gdal_translate, clip to Chennai bbox
# providers/file_terrain.py → reads GeoTIFF
```

---

### 3. Drainage Network — `SyntheticDrainageProvider`

**File:** `backend/app/providers/synthetic_drainage.py`

30 prototype nodes with:
- Type: INLET / PIPE / JUNCTION / OUTLET / PUMP / STORAGE
- Capacity in `m³/s`
- Inflow computed from SCS-CN runoff
- Utilization = inflow / capacity × 100

**Real replacement path:**
```python
# Connect CMWSSB SCADA system
# Each node → real sensor reading
# SWMM solver for full hydraulic routing
```

---

### 4. Road Network — NetworkX Graph

**File:** `backend/app/services/routing/graph.py`

22 synthetic road nodes across Chennai with 58 directed edges.

**Real replacement path:**
```python
import osmnx as ox
G = ox.graph_from_place("Chennai, India", network_type="drive")
# 50,000+ nodes, flood-weight edge attributes applied dynamically
```

---

## Feature Engineering (ML Layer)

The 14 ML features are computed from the above data sources:

| Feature | Source | Notes |
|---------|--------|-------|
| `rainfall_intensity_mm_hr` | Rainfall provider | Primary predictor |
| `rainfall_duration_hr` | Simulation timer | Time since rain started |
| `accumulated_rainfall_mm` | Running integral | Antecedent wetness |
| `drainage_utilization_pct` | Drainage provider | Avg across 30 nodes |
| `drainage_surcharging_nodes` | Drainage provider | Count > 100% util |
| `catchment_imperviousness` | Terrain / lookup | Urban fraction |
| `catchment_cn` | Terrain / AMC | SCS Curve Number |
| `catchment_area_ha` | Static | Per catchment |
| `terrain_elevation_m` | Terrain provider | Mean elevation |
| `terrain_slope_pct` | Terrain provider | Mean slope |
| `terrain_susceptibility` | Terrain provider | Weighted composite |
| `antecedent_moisture_mm` | AMC model | 5-day precip proxy |
| `time_since_last_rain_hr` | Simulation state | Dry period duration |
| `horizon_minutes` | Nowcast engine | T+0 to T+180 |

---

## Data Provenance

Every API response includes:
```json
{
  "data_source": "SYNTHETIC_PROTOTYPE",
  "model_version": "v1",
  "timestamp": "2026-09-05T14:30:00Z"
}
```

This is a hard engineering requirement — no synthetic data is ever presented as real.

---

## WebSocket Data Flow

```
SimulationEngine.tick()
        │
        ├── SyntheticRainfallProvider.update(intensity)
        ├── SCS_CN.compute_runoff(intensity, catchments)
        ├── DrainageProvider.compute_utilization(runoff)
        ├── NowcastEngine.generate_nowcasts()
        │       └── MLPredictor.predict(14 features × 9 horizons × 12 locations)
        ├── RiskEngine.score(nowcasts, drainage)
        ├── AlertEngine.evaluate(risk_states)
        ├── DecisionEngine.generate(hydraulic_state)
        └── WSManager.broadcast(tick_payload)
                └── → All connected WebSocket clients
```

Tick interval: **5 seconds** (configurable via `WS_BROADCAST_INTERVAL`)
