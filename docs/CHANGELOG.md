# FLOOD-X — Changelog

All notable changes to this project are documented here.  
Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

---

## [0.1.0] — 2026-09-06 · SIH 2026 Submission

### Added

#### Core Backend
- FastAPI application with 16 registered API routes under `/api/v1`
- WebSocket real-time broadcast at `/ws` with 5-second simulation tick
- Pydantic v2 schemas with `DataProvenance` field on all responses
- `SYNTHETIC_PROTOTYPE` label enforced on every endpoint response
- Graceful PostgreSQL fallback — system runs in SIMULATION mode without DB

#### ML Pipeline
- XGBoost Classifier: flood_occurred binary classification (97.38% accuracy, AUC 99.79%)
- XGBoost Regressor: flood_depth_cm estimation (R²=0.9948, MAE=10.64cm)
- 14-feature engineering pipeline (rainfall, drainage, terrain, antecedent moisture)
- Deterministic training: 8000 samples, seed=42, fully reproducible
- `scripts/train_models.py` — 6-step training pipeline with printed metrics
- Feature importance explainability via `/api/v1/explain/feature-importance`
- Per-prediction SHAP-approximation via `/api/v1/explain/prediction`

#### Hydrology Engine
- SCS-CN method: AMC-I/II/III antecedent moisture adjustment
- Rational Method peak flow: Q = CiA/360
- Kirpich (1940) time of concentration formula
- 12 synthetic catchments representing Chennai Metropolitan Area

#### Drainage Network
- 30-node synthetic drainage prototype (INLET, PIPE, JUNCTION, OUTLET, PUMP, STORAGE)
- Utilization computation via Rational Method inflow vs pipe capacity
- Surcharge detection (>100% utilization)
- Bottleneck identification and directed graph connectivity

#### Nowcast Engine
- 9 prediction horizons: T+0, T+15, T+30, T+45, T+60, T+90, T+120, T+150, T+180 min
- Per-horizon confidence decay function
- Flood Clock: time-to-critical prediction per location (SAFE → WATCH → WARNING → CRITICAL)

#### Risk Engine
- 5-component transparent weighted scoring system
- Weights: flood_probability(35%) + drainage(25%) + depth(20%) + rainfall(12%) + terrain(8%)
- Documented thresholds: LOW(<0.30), MODERATE(0.30–0.55), HIGH(0.55–0.80), CRITICAL(≥0.80)

#### Alert Engine
- IMD-aligned 4-tier severity: INFO / WATCH / WARNING / EMERGENCY
- Threshold-based triggering (intensity, drainage util, flood probability)

#### Decision Support Engine
- 7 NDMA-aligned recommendation categories
- Priority ranking by urgency (IMMEDIATE → HIGH → MODERATE → LOW)
- Per-recommendation: title, rationale, action_steps, deadline_minutes, confidence
- Disclaimer on every recommendation: "DECISION-SUPPORT ONLY"

#### Safe Routing
- NetworkX directed weighted graph (22 nodes, 58 edges)
- Dijkstra flood-aware routing with dynamic edge penalties
- Flood risk multipliers: LOW(1.0×), MODERATE(1.5×), HIGH(3.0×), CRITICAL(10.0×)
- Dual route comparison: flood_aware vs normal returned together

#### Simulation Engine
- 8 scenarios: normal_rainfall, heavy_rainfall, extreme_rainfall, short_intense_storm,
  prolonged_rainfall, drainage_blockage, pump_failure, combined_extreme
- 13 phase labels (System Normal → Pre-storm → Rainfall Intensifying → Peak → ...)
- Pause / Resume / Reset controls
- Speed multiplier (0.1× to 10×)

#### Demo Mode
- Deterministic demo orchestrator for SIH presentation
- Auto-progressing phases with narration
- `/demo/start|status|reset|phases` endpoints

#### Frontend (React 19 + TypeScript)
- 11 pages: Command Center, Live Flood Map, Nowcast, Drainage Network, Flood Clock,
  Safe Routing, Alerts & Decisions, Simulation Center, Data & Confidence, System Health,
  Methodology
- MapLibre GL JS with 7 data layers (risk zones, polygons, drainage nodes, safe route...)
- Zustand global state, useWebSocket auto-reconnect hook
- Recharts for nowcast timeline, XGBoost feature importance bar chart
- Full dark theme with risk-level colour system

#### ORM Models (M8)
- `FloodEvent` — per-location, per-horizon prediction record
- `AlertLog` — alert audit trail
- `SimulationRun` — simulation execution record
- Alembic migration: `database/migrations/versions/0001_initial_tables.py`

#### Testing (M9)
- 43 unit tests: hydrology, ML predictor, risk engine, routing
- 27 API tests: all 16 routes tested with httpx AsyncClient
- 8 integration tests: full simulation lifecycle (start/pause/resume/reset)
- Total: **78 tests, 0 failures**

#### Documentation (M10)
- 18 documents covering: Architecture, ML Model Card, Methodology, QUICKSTART,
  Deployment Guide, API Reference, Data Pipeline, Real Data Upgrade, Testing Guide,
  Drainage Network Spec, Road Network Spec, Configuration Guide, Known Limitations,
  Security, SIH Pitch, SIH Judge Q&A, Project Audit, Changelog

### Technical Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI 0.115, XGBoost 2.1, NetworkX 3.4, SQLAlchemy 2.0 |
| Frontend | React 19, TypeScript, Zustand, MapLibre GL JS, Recharts |
| Infrastructure | Docker Compose, PostgreSQL 16 + PostGIS 3.4, WebSocket |
| Testing | pytest 8.3, pytest-asyncio, httpx |
| ML | XGBoost, scikit-learn, NumPy, pandas |
| Geospatial | NetworkX, Shapely, pyproj |

---

## [0.0.1] — 2026-09-05 · Initial Commit

- Initial project structure: backend, frontend, docker, scripts, docs directories
- FastAPI scaffold with CORS, GZip middleware
- Pydantic schemas: 16 models with DataProvenance
- docker-compose.yml with 3 services
- `.env.example` with full variable documentation
