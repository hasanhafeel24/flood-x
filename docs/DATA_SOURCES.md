# FLOOD-X — Data Sources

> Documents every data source used in the system: what it is, where it comes from,
> how it is used, and the real-data upgrade path.
>
> **ALL sources in this prototype are `SYNTHETIC_PROTOTYPE` unless explicitly stated otherwise.**

---

## 1. Rainfall Data

| Attribute | Value |
|-----------|-------|
| **Source** | `SyntheticRainfallProvider` |
| **Type** | SYNTHETIC_PROTOTYPE |
| **File** | `backend/app/providers/synthetic_rainfall.py` |
| **Update rate** | Every simulation tick (5s) |
| **Format** | JSON: intensity_mm_hr, category, accumulated_mm |
| **Coverage** | Single point (Chennai centroid: 13.0827°N, 80.2707°E) |

**What it provides:** Intensity driven by `SimulationEngine.set_rainfall_intensity()` based on the chosen scenario (normal_rainfall: ~8mm/hr to combined_extreme: ~95mm/hr).

**Real-data path:**
- IMD AWS station 43279 (Chennai Airport) — 15-min rainfall telemetry
- IMD API: `https://api.imd.gov.in/rainfall/current`
- Config: `RAINFALL_PROVIDER=imd`, `IMD_API_KEY=<key>`

---

## 2. Terrain / DEM Data

| Attribute | Value |
|-----------|-------|
| **Source** | `SyntheticTerrainProvider` |
| **Type** | SYNTHETIC_PROTOTYPE |
| **File** | `backend/app/providers/synthetic_terrain.py` |
| **Coverage** | 12 synthetic catchments |

**What it provides:** Per-catchment elevation (m), slope (%), soil type (B/C/D), susceptibility score derived from published Chennai urban studies.

**Real-data path:**
- SRTM 30m DEM: `https://earthexplorer.usgs.gov/` (Tile N12E080, public domain)
- Process with GDAL: `gdal_translate -projwin 80.0 13.2 80.4 12.8`
- Config: `TERRAIN_PROVIDER=file`, `DEM_FILE_PATH=data/terrain/chennai_dem_30m.tif`

---

## 3. Drainage Network Data

| Attribute | Value |
|-----------|-------|
| **Source** | `SyntheticDrainageProvider` |
| **Type** | SYNTHETIC_PROTOTYPE |
| **File** | `backend/app/providers/synthetic_drainage.py` |
| **Nodes** | 30 |
| **Node types** | INLET, PIPE, JUNCTION, OUTLET, PUMP, STORAGE |

**What it provides:** Per-node capacity (m³/s), inflow from Rational Method, utilization (%), surcharge status, coordinates.

**Basis:** Approximated from published Chennai urban drainage studies (CMWSSB Annual Reports, Chennai Flood Management Plan 2018) and Indian standard design parameters (IS:4948, CPHEEO Manual).

**Real-data path:**
- CMWSSB SCADA system (500+ monitored points)
- Requires data-sharing MoU
- Config: `DRAINAGE_PROVIDER=cmwssb`, `CMWSSB_TOKEN=<token>`

---

## 4. Road Network

| Attribute | Value |
|-----------|-------|
| **Source** | Hardcoded synthetic graph |
| **Type** | SYNTHETIC_PROTOTYPE |
| **File** | `backend/app/services/routing/graph.py` |
| **Nodes** | 22 |
| **Edges** | 58 directed |

**What it provides:** Representative Chennai road junctions with travel time, distance, flood susceptibility attributes. Flood-weight penalties applied dynamically.

**Real-data path:**
- `osmnx.graph_from_place("Chennai, India")` → 50,000+ nodes, 120,000+ edges
- `networkx` Dijkstra scales to full OSM graph

---

## 5. ML Training Data

| Attribute | Value |
|-----------|-------|
| **Source** | `SyntheticDataGenerator` |
| **Type** | SYNTHETIC_PROTOTYPE (physics-simulation-generated) |
| **File** | `backend/app/services/ml/data_generator.py` |
| **Samples** | 8,000 |
| **Seed** | 42 (deterministic) |

**What it provides:** 14-feature training dataset where labels (`flood_occurred`, `flood_depth_cm`) are derived from SCS-CN hydrology physics, not observed real events.

**Generation logic:**
1. Sample rainfall intensity from realistic distributions per IMD category
2. Run SCS-CN to compute runoff
3. Compute drainage utilization from Rational Method
4. Apply flood depth model based on catchment characteristics
5. Add controlled noise (σ=0.05) for realism

**Real-data path:**
- IMD historical rainfall records (2000–2025)
- CMWSSB historical sensor logs
- Satellite inundation maps (Sentinel-1 SAR, NASA MODIS Flood)
- Chennai Corporation flood depth observations (2015, 2021 events)

---

## 6. Geographic Reference Data

| Data | Source | Status |
|------|--------|--------|
| Chennai district boundary | OpenStreetMap / Census 2011 | NOT loaded (would use osmnx) |
| Catchment boundaries | Synthetic bounding boxes | SYNTHETIC_PROTOTYPE |
| Ward boundaries | Chennai Corporation GIS | NOT available |
| River/canal network | Synthetic | SYNTHETIC_PROTOTYPE |

---

## 7. External Standards Referenced

These are real standards that informed the prototype design — not data sources:

| Standard | Usage |
|----------|-------|
| **USDA SCS-CN** | Runoff estimation methodology |
| **IS:4987** | Indian urban drainage design |
| **CPHEEO Manual** | Urban drainage capacity sizing |
| **IMD Rainfall Categories** | Alert threshold alignment |
| **NDMA Guidelines** | Decision support framework |
| **Kirpich (1940)** | Time of concentration formula |
| **Rational Method (Q=CiA/360)** | Peak flow estimation |

---

## 8. Data Provenance Summary

| Source | Label | Used In |
|--------|-------|---------|
| SyntheticRainfallProvider | SYNTHETIC_PROTOTYPE | All predictions |
| SyntheticTerrainProvider | SYNTHETIC_PROTOTYPE | Feature engineering, risk |
| SyntheticDrainageProvider | SYNTHETIC_PROTOTYPE | Surcharge, drainage status |
| ML training data | SYNTHETIC_PROTOTYPE | Model training |
| Road graph | SYNTHETIC_PROTOTYPE | Routing |
| USDA SCS-CN formula | REAL (public domain method) | Hydrology engine |
| IMD thresholds | REAL (published standard) | Alert classification |
| NDMA framework | REAL (published guideline) | Decision engine |
