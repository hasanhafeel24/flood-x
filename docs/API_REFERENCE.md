# FLOOD-X — API Reference

> **Base URL:** `http://localhost:8000/api/v1`  
> **Interactive docs:** `http://localhost:8000/api/docs` (Swagger UI)  
> **WebSocket:** `ws://localhost:8000/ws`  
> **Data source:** All responses include `"data_source": "SYNTHETIC_PROTOTYPE"` unless noted.

---

## Authentication

No authentication required for the prototype. Production deployment should add JWT bearer tokens.

---

## Endpoints

### Health

#### `GET /health`
System liveness check.

**Response:**
```json
{ "status": "ok", "service": "FLOOD-X API", "version": "0.1.0" }
```

---

### Rainfall

#### `GET /rainfall/current`
Current rainfall observation.

**Response:**
```json
{
  "intensity_mm_hr": 45.2,
  "category": "HEAVY",
  "accumulated_mm": 78.4,
  "timestamp": "2026-09-05T14:30:00Z",
  "data_source": "SYNTHETIC_PROTOTYPE"
}
```

#### `GET /rainfall/forecast?hours=3`
0–3 hour rainfall forecast at 15-minute intervals.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `hours` | int | `3` | Forecast window (1–3 hours) |

**Response:** Array of `RainfallObservation` objects.

---

### Flood Nowcast

#### `GET /flood/nowcast`
0–3 hour flood nowcast for all 12 pilot catchments.

**Response:** Array of `LocationNowcast` objects.
```json
[
  {
    "location_id": "C001",
    "location_name": "Velachery Basin",
    "latitude": 12.985,
    "longitude": 80.215,
    "current_risk": "HIGH",
    "current_depth_cm": 28.4,
    "risk_score": 0.72,
    "flood_clock": {
      "status": "WARNING",
      "minutes_to_critical": 35
    },
    "horizons": [
      {
        "horizon_minutes": 0,
        "flood_probability": 0.81,
        "estimated_depth_cm": 28.4,
        "confidence": 0.92
      }
      // ... T+15, T+30, T+45, T+60, T+90, T+120, T+150, T+180
    ],
    "data_source": "SYNTHETIC_PROTOTYPE"
  }
]
```

#### `GET /flood/zones`
Current flood risk zones as **GeoJSON FeatureCollection (Points)**.

#### `GET /flood/zones/polygons`
Catchment flood risk zones as **GeoJSON FeatureCollection (Polygons)**.

#### `GET /flood/location/{location_id}`
Detailed nowcast for a single location.

**Path params:** `location_id` — e.g. `C001` through `C012`

**Errors:** `404` if location not found.

#### `GET /flood/clock/{location_id}`
Flood Clock — time-to-critical prediction.

**Response:**
```json
{
  "location_id": "C001",
  "location_name": "Velachery Basin",
  "status": "WARNING",
  "current_depth_cm": 28.4,
  "minutes_to_watch": 0,
  "minutes_to_warning": 0,
  "minutes_to_critical": 35,
  "trajectory": "WORSENING"
}
```

---

### Drainage Network

#### `GET /drainage/status`
Current network-wide drainage summary.

**Response:**
```json
{
  "overall_status": "HIGH",
  "average_utilization_pct": 87.3,
  "surcharging_nodes": 4,
  "bottleneck_nodes": ["DN001", "DN007"],
  "data_source": "SYNTHETIC_PROTOTYPE"
}
```

#### `GET /drainage/nodes`
All 30 drainage nodes with current utilization.

**Response:** Array of `DrainageNode` objects.

---

### Safe Routing

#### `GET /routes/safe`
Flood-aware Dijkstra route between two points.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `orig_lat` | float | `13.0827` | Origin latitude |
| `orig_lon` | float | `80.2707` | Origin longitude |
| `dest_lat` | float | `12.9716` | Destination latitude |
| `dest_lon` | float | `80.2430` | Destination longitude |
| `flood_aware` | bool | `true` | Use flood-aware routing |

**Response:**
```json
{
  "flood_aware_route": {
    "waypoints": [...],
    "distance_km": 12.4,
    "estimated_time_min": 28,
    "flood_zones_avoided": 2,
    "risk_level": "LOW"
  },
  "normal_route": { ... },
  "data_source": "SYNTHETIC_PROTOTYPE"
}
```

#### `GET /routes/graph-info`
Road network graph statistics.

---

### Alerts

#### `GET /alerts`
All currently active alerts.

**Response:** Array of `Alert` objects with fields:
`alert_id`, `severity` (INFO/WATCH/WARNING/EMERGENCY), `title`, `description`, `location_name`, `latitude`, `longitude`, `issued_at`, `recommended_action`, `confidence`.

---

### Decision Support

#### `GET /decisions/current`
AI-generated ranked decision recommendations for the current hydraulic state.

**Response:**
```json
{
  "package_id": "PKG-2026-...",
  "issued_at": "2026-09-05T14:30:00Z",
  "overall_risk": "HIGH",
  "situation_summary": "Drainage network under stress...",
  "total_recommendations": 4,
  "immediate_actions": 1,
  "recommendations": [
    {
      "rec_id": "REC-001",
      "category": "drainage_operations",
      "urgency": "IMMEDIATE",
      "priority_rank": 1,
      "title": "Activate emergency pump capacity",
      "rationale": "...",
      "action_steps": ["...", "..."],
      "deadline_minutes": 15,
      "confidence": 0.87,
      "data_source": "SYNTHETIC_PROTOTYPE",
      "disclaimer": "DECISION-SUPPORT ONLY — not an official emergency order"
    }
  ],
  "data_source": "SYNTHETIC_PROTOTYPE",
  "disclaimer": "..."
}
```

---

### Explainability

#### `GET /explain/feature-importance`
XGBoost global feature importance (gain).

**Response:**
```json
{
  "features": [
    { "rank": 1, "feature": "rainfall_intensity_mm_hr", "label": "Rainfall Intensity", "importance": 0.3449, "importance_pct": 34.49 },
    ...
  ],
  "model_version": "v1",
  "importance_type": "gain",
  "data_source": "SYNTHETIC_PROTOTYPE"
}
```

#### `GET /explain/prediction`
Per-feature contributions for a specific prediction scenario.

**Query params:** `intensity`, `accumulated`, `utilization`, `surcharging`, `horizon_minutes`

---

### Simulation

#### `POST /simulation/start`
Start a simulation scenario.

**Body:**
```json
{ "scenario": "extreme_rainfall", "speed": 1.0 }
```

**Scenarios:** `normal_rainfall`, `heavy_rainfall`, `extreme_rainfall`, `short_intense_storm`, `prolonged_rainfall`, `drainage_blockage`, `pump_failure`, `combined_extreme`

#### `POST /simulation/pause` / `POST /simulation/resume` / `POST /simulation/reset`
Control simulation playback.

#### `GET /simulation/state`
Current simulation state.

#### `GET /simulation/scenarios`
List all available scenarios with metadata.

---

### Demo Mode

#### `POST /demo/start`
Start the deterministic SIH demo scenario (extreme_rainfall, auto-progressing).

#### `GET /demo/status`
Current demo status and phase.

#### `GET /demo/phases`
All demo phases with timestamps and narration.

#### `POST /demo/reset`
Reset demo to initial state.

---

### System

#### `GET /system/status`
System health, provider status, ML model status.

---

## WebSocket

### `WS /ws`

Real-time simulation event stream. Broadcasts every 5 seconds during active simulation.

**Message types:**

#### `simulation_tick`
```json
{
  "type": "simulation_tick",
  "timestamp": "2026-09-05T14:30:05Z",
  "phase": "PEAK_RAINFALL",
  "rainfall": {
    "intensity_mm_hr": 85.2,
    "accumulated_mm": 124.8
  },
  "simulation": { "run_id": "...", "is_running": true, "scenario": "...", ... },
  "drainage": { "overall_status": "CRITICAL", "average_utilization_pct": 112.4, ... },
  "alerts": [...],
  "nowcast_zones": [
    { "location_id": "C001", "risk": "HIGH", "depth_cm": 28.4, "prob_60min": 0.81 },
    ...
  ],
  "data_mode": "SYNTHETIC_SIMULATION"
}
```

#### `simulation_reset`
```json
{ "type": "simulation_reset" }
```

---

## Error Responses

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request (invalid parameters) |
| `404` | Resource not found |
| `422` | Validation error (Pydantic schema) |
| `500` | Internal server error |

All errors return:
```json
{ "detail": "Human-readable error message" }
```
