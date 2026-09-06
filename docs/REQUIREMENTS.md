# FLOOD-X — System Requirements

> Derived from SIH26085 problem statement.  
> Document type: REQUIREMENTS (not a claim of delivery — see TRACEABILITY.md for implementation status)

---

## 1. Functional Requirements

### FR01 — Rainfall Integration
- System SHALL accept rainfall intensity (mm/hr) as primary input
- System SHALL classify rainfall by IMD categories: Light (<2.5), Moderate (2.5–64.4), Heavy (64.5–115.5), Extreme (>115.5 mm/hr)
- System SHALL support 0–3 hour rainfall forecasting
- Data source SHALL be clearly labelled (REAL / SYNTHETIC)

### FR02 — Drainage Coupling
- System SHALL model drainage network capacity and loading
- System SHALL detect surcharging conditions (utilization > 100%)
- System SHALL identify bottleneck nodes
- System SHALL compute drainage utilization from rainfall-runoff inputs

### FR03 — Hydrology Engine
- System SHALL compute surface runoff using SCS-CN method
- System SHALL apply antecedent moisture condition (AMC) adjustments
- System SHALL compute time of concentration using Kirpich formula
- System SHALL compute peak flow using Rational Method

### FR04 — Flood Prediction
- System SHALL produce 0–3 hour flood probability predictions
- System SHALL estimate flood depth in cm for flooded locations
- System SHALL produce predictions at 9 time horizons (T+0, T+15, T+30, T+45, T+60, T+90, T+120, T+150, T+180)
- System SHALL assign confidence to each prediction

### FR05 — Flood Clock
- System SHALL compute time-to-critical (minutes until WARNING/CRITICAL threshold)
- System SHALL classify current trajectory: SAFE / WATCH / WARNING / CRITICAL
- Flood Clock SHALL update with every simulation tick

### FR06 — Risk Classification
- System SHALL assign risk level: LOW / MODERATE / HIGH / CRITICAL
- Risk SHALL be computed from ≥5 weighted components
- Risk weights and thresholds SHALL be documented and transparent

### FR07 — Alert Engine
- System SHALL generate alerts at 4 severity levels: INFO / WATCH / WARNING / EMERGENCY
- Alert thresholds SHALL align with IMD and NDMA standards
- Every alert SHALL include recommended action and confidence score

### FR08 — Decision Support
- System SHALL generate ranked decision recommendations
- Recommendations SHALL cover ≥5 response categories
- Every recommendation SHALL include: urgency, rationale, action steps, deadline, confidence
- Every recommendation SHALL carry a disclaimer: "DECISION-SUPPORT ONLY"

### FR09 — Flood-Aware Routing
- System SHALL build a directed road graph with flood-risk weighted edges
- System SHALL compute flood-aware shortest path using Dijkstra
- System SHALL return: route geometry, distance, ETA, max flood depth, risk, warnings
- System SHALL return both flood-aware and normal routes for comparison

### FR10 — Real-Time Dashboard
- Dashboard SHALL answer: WHERE? HOW BAD? HOW DEEP? HOW SOON? WHAT TO DO?
- Dashboard SHALL show live flood risk zones on a GIS map
- Dashboard SHALL update via WebSocket (≤10s latency)
- Dashboard SHALL show system state: LIVE / SIMULATION / STALE / DISCONNECTED

### FR11 — Flood Zone Generation
- System SHALL generate flood zone GeoJSON from model outputs
- Flood zone polygons SHALL reflect actual risk/depth per catchment
- System SHALL provide both Point and Polygon GeoJSON representations

### FR12 — Data Provenance
- Every API response SHALL include a `data_source` field
- All synthetic/simulated data SHALL be explicitly labelled `SYNTHETIC_PROTOTYPE`
- System SHALL NEVER label synthetic data as real

### FR13 — REST API
- System SHALL expose all data via versioned REST API (`/api/v1/*`)
- API SHALL include Swagger/OpenAPI documentation
- All endpoints SHALL validate inputs and return structured errors

### FR14 — WebSocket
- System SHALL broadcast simulation state via WebSocket
- WebSocket SHALL auto-reconnect on disconnect
- WebSocket SHALL include heartbeat mechanism
- WebSocket SHALL detect and signal stale data

### FR15 — Deterministic Demo
- System SHALL support a reproducible demo mode (seed=42)
- Demo SHALL auto-progress through ≥6 phases
- Demo SHALL be controllable: start / pause / resume / reset

---

## 2. Non-Functional Requirements

### NFR01 — Performance
- API response time: < 500ms for all endpoints (p95)
- WebSocket tick latency: ≤ 5 seconds
- ML inference time: < 200ms per full nowcast (12 locations × 9 horizons)

### NFR02 — Reliability
- System SHALL operate without PostgreSQL (degraded simulation mode)
- System SHALL operate without internet (fully offline capable)
- System SHALL handle provider failures with graceful degradation

### NFR03 — Security
- No secrets in source code or committed files
- CORS restricted to configured origins
- All inputs validated via Pydantic v2
- Database operations via parameterized ORM queries

### NFR04 — Reproducibility
- ML training SHALL be deterministic (seed=42)
- Demo mode SHALL produce identical output every run

### NFR05 — Observability
- Structured JSON logs (structlog)
- All data sources labelled on every response
- System status endpoint: `/api/v1/system/status`
- WebSocket connection state visible in UI

### NFR06 — Deployability
- System SHALL be runnable with a single `docker compose up`
- System SHALL run locally without Docker (development mode)
- System SHALL require no proprietary external services

---

## 3. Out of Scope (Current Prototype)

- Real-time IMD radar/satellite data ingestion
- Real CMWSSB SCADA integration
- Full pipe hydraulic simulation (SWMM)
- Real-world flood event validation
- OSM full road network (50,000+ nodes)
- User authentication and authorization
- Multi-city deployment
- Historical data storage and playback
