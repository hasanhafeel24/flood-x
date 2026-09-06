# FLOOD-X — Data Dictionary

> Defines every field in every API response and database model.  
> Units, types, ranges, and data source for each field.

---

## API Response Fields

### RainfallObservation

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `intensity_mm_hr` | float | mm/hr | 0–300 | SYNTHETIC_PROTOTYPE |
| `category` | enum | — | LIGHT/MODERATE/HEAVY/EXTREME | Derived from intensity |
| `accumulated_mm` | float | mm | 0–∞ | Cumulative since sim start |
| `timestamp` | ISO8601 | UTC | — | System clock |
| `latitude` | float | degrees | 8.0–37.0 (India) | Chennai pilot centroid |
| `longitude` | float | degrees | 68.0–97.0 (India) | Chennai pilot centroid |

---

### LocationNowcast

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `location_id` | string | — | C001–C012 | Synthetic catchment ID |
| `location_name` | string | — | — | Catchment name |
| `latitude` | float | degrees WGS84 | — | Catchment centroid |
| `longitude` | float | degrees WGS84 | — | Catchment centroid |
| `current_risk` | enum | — | LOW/MODERATE/HIGH/CRITICAL | RiskEngine output |
| `current_depth_cm` | float | cm | 0–∞ | ML Regressor output |
| `risk_score` | float | — | 0.0–1.0 | Weighted 5-component score |
| `horizons` | array | — | 9 items | NowcastEngine |

---

### NowcastHorizon

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `horizon_minutes` | int | min | 0, 15, 30, 45, 60, 90, 120, 150, 180 | Fixed horizons |
| `flood_probability` | float | — | 0.0–1.0 | XGBoost Classifier |
| `estimated_depth_cm` | float | cm | 0.0–∞ | XGBoost Regressor (zero-clipped) |
| `confidence` | float | — | 0.0–1.0 | Decays with horizon distance |
| `risk_level` | enum | — | LOW/MODERATE/HIGH/CRITICAL | Thresholded from probability |

---

### FloodClock

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `location_id` | string | — | C001–C012 | — |
| `location_name` | string | — | — | — |
| `clock_status` | enum | — | SAFE/WATCH/WARNING/CRITICAL | From horizon scan |
| `current_depth_cm` | float | cm | 0–∞ | Current nowcast |
| `minutes_to_watch` | int\|null | min | 0–180 | First horizon exceeding WATCH threshold |
| `minutes_to_warning` | int\|null | min | 0–180 | First horizon exceeding WARNING threshold |
| `minutes_to_critical` | int\|null | min | 0–180 | First horizon exceeding CRITICAL threshold |

**Depth thresholds:**
| Threshold | Depth |
|-----------|-------|
| WATCH | ≥ 5 cm |
| WARNING | ≥ 20 cm |
| CRITICAL | ≥ 45 cm |

---

### DrainageNetworkStatus

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `overall_status` | enum | — | LOW/MODERATE/HIGH/CRITICAL | Derived from avg utilization |
| `average_utilization_pct` | float | % | 0–∞ | Mean across 30 nodes |
| `surcharging_nodes` | int | — | 0–30 | Count with util > 100% |
| `bottleneck_nodes` | list[str] | — | node IDs | Highest utilization nodes |

---

### DrainageNode

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `node_id` | string | — | N001–N030 | Synthetic node ID |
| `node_type` | enum | — | INLET/PIPE/JUNCTION/OUTLET/PUMP/STORAGE | Node classification |
| `utilization_pct` | float | % | 0–∞ | inflow/capacity × 100 |
| `is_surcharging` | bool | — | — | utilization_pct > 100 |
| `capacity_m3s` | float | m³/s | 0.05–15 | Designed pipe capacity |
| `latitude` | float | ° | — | Node centroid |
| `longitude` | float | ° | — | Node centroid |

---

### RouteResponse

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `route_id` | string | — | UUID | Generated per request |
| `is_flood_aware` | bool | — | — | true = flood-weighted Dijkstra |
| `distance_km` | float | km | 0–∞ | Sum of edge distances |
| `estimated_travel_min` | float | min | 0–∞ | Sum of (flood-weighted) edge times |
| `max_predicted_depth_cm` | float | cm | 0–∞ | Max depth on route edges |
| `max_risk_level` | enum | — | LOW/MODERATE/HIGH/CRITICAL | Worst edge risk |
| `flood_zones_avoided` | int | — | 0–∞ | vs normal route (flood-aware only) |
| `waypoints` | list[{lat,lon}] | ° | — | Route node coordinates |
| `note` | string | — | — | Route selection explanation |

---

### Alert

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `alert_id` | string | — | UUID | AlertEngine |
| `severity` | enum | — | INFO/WATCH/WARNING/EMERGENCY | IMD-aligned thresholds |
| `title` | string | — | — | AlertEngine templates |
| `description` | string | — | — | AlertEngine templates |
| `location_name` | string | — | — | Catchment name |
| `latitude` | float | ° | — | Alert origin |
| `longitude` | float | ° | — | Alert origin |
| `issued_at` | ISO8601 | UTC | — | System clock |
| `confidence` | float | — | 0.0–1.0 | From RiskEngine |
| `recommended_action` | string | — | — | Decision support |

---

### DecisionRecommendation

| Field | Type | Unit | Range | Source |
|-------|------|------|-------|--------|
| `rec_id` | string | — | UUID | DecisionEngine |
| `category` | enum | — | 7 categories | NDMA classification |
| `urgency` | enum | — | IMMEDIATE/HIGH/MODERATE/LOW | Risk-derived |
| `priority_rank` | int | — | 1–N | Ranked by urgency |
| `title` | string | — | — | Template |
| `rationale` | string | — | — | Risk state explanation |
| `action_steps` | list[str] | — | — | Specific actions |
| `deadline_minutes` | int\|null | min | — | Urgency deadline |
| `confidence` | float | — | 0.0–1.0 | From risk score |
| `data_source` | string | — | SYNTHETIC_PROTOTYPE | Provenance |
| `disclaimer` | string | — | — | "DECISION-SUPPORT ONLY — not official emergency orders" |

---

## ML Feature Dictionary

| Feature | Description | Unit | Source | Importance |
|---------|-------------|------|--------|-----------|
| `rainfall_intensity_mm_hr` | Current rainfall rate | mm/hr | RainfallProvider | 34.5% |
| `accumulated_rainfall_mm` | Cumulative rainfall | mm | Running total | 33.2% |
| `rainfall_duration_hr` | Time since rain started | hr | Simulation timer | 7.6% |
| `drainage_surcharging_nodes` | Count of nodes >100% | count | DrainageProvider | 5.1% |
| `catchment_imperviousness` | Urban surface fraction | 0–1 | Catchment lookup | 4.8% |
| `catchment_cn` | SCS Curve Number | — | AMC-adjusted | 3.9% |
| `catchment_area_ha` | Catchment area | hectares | Static | 3.2% |
| `terrain_elevation_m` | Mean catchment elevation | m | TerrainProvider | 2.8% |
| `drainage_utilization_pct` | Mean drainage loading | % | DrainageProvider | 2.1% |
| `terrain_slope_pct` | Mean slope | % | TerrainProvider | 1.5% |
| `terrain_susceptibility` | Weighted susceptibility | 0–1 | TerrainProvider | 1.3% |
| `antecedent_moisture_mm` | 5-day precip proxy | mm | AMC model | 1.1% |
| `time_since_last_rain_hr` | Dry period duration | hr | Simulation state | 0.8% |
| `horizon_minutes` | Forecast horizon | min | NowcastEngine | 0.5% |

---

## Database Column Dictionary

### flood_events

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL PK | No | Auto-increment |
| `location_id` | VARCHAR(10) | No | C001–C012 |
| `location_name` | VARCHAR(100) | No | Catchment name |
| `latitude` | FLOAT | No | WGS84 |
| `longitude` | FLOAT | No | WGS84 |
| `recorded_at` | TIMESTAMPTZ | No | UTC prediction time |
| `horizon_minutes` | INTEGER | No | 0–180 |
| `flood_probability` | FLOAT | No | 0.0–1.0 |
| `estimated_depth_cm` | FLOAT | No | ≥0 |
| `current_risk` | ENUM | No | risk_level_enum |
| `rainfall_intensity_mm_hr` | FLOAT | Yes | Feature at prediction time |
| `drainage_utilization_pct` | FLOAT | Yes | Feature at prediction time |
| `data_source` | VARCHAR(50) | No | SYNTHETIC_PROTOTYPE |
| `run_id` | VARCHAR(50) | Yes | FK to simulation_runs |

### alert_logs

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL PK | No | — |
| `alert_id` | VARCHAR(50) UNIQUE | No | UUID |
| `severity` | ENUM | No | alert_severity_enum |
| `title` | VARCHAR(200) | No | — |
| `description` | TEXT | Yes | — |
| `issued_at` | TIMESTAMPTZ | No | UTC |
| `expires_at` | TIMESTAMPTZ | Yes | — |
| `confidence` | FLOAT | No | 0.0–1.0 |
| `acknowledged` | BOOLEAN | No | Default false |
| `data_source` | VARCHAR(50) | No | SYNTHETIC_PROTOTYPE |

### simulation_runs

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL PK | No | — |
| `run_id` | VARCHAR(50) UNIQUE | No | UUID |
| `scenario` | VARCHAR(100) | No | Scenario name |
| `speed` | FLOAT | No | Playback multiplier |
| `started_at` | TIMESTAMPTZ | No | UTC |
| `ended_at` | TIMESTAMPTZ | Yes | NULL if still running |
| `total_steps` | INTEGER | No | Tick count |
| `peak_rainfall_mm_hr` | FLOAT | Yes | Max intensity recorded |
| `completed` | BOOLEAN | No | True if natural end |
| `data_source` | VARCHAR(50) | No | SYNTHETIC_PROTOTYPE |
