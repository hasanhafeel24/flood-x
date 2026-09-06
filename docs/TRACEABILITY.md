# FLOOD-X — Traceability Matrix

> Maps every SIH26085 requirement to its FLOOD-X implementation, test, and demo evidence.
> `Last updated: 2026-09-06`

---

## SIH26085 Problem Statement Requirements

| # | Requirement | Component | File(s) | Test(s) | Demo Evidence |
|---|-------------|-----------|---------|---------|---------------|
| R01 | Integrate rainfall data as primary input | `SyntheticRainfallProvider` | `providers/synthetic_rainfall.py` | `test_endpoints.py::test_rainfall_current` | Simulation Center → intensity gauge |
| R02 | Couple rainfall with urban drainage system | `SyntheticDrainageProvider` + SCS-CN | `providers/synthetic_drainage.py`, `services/hydrology/engine.py` | `test_hydrology.py` | Drainage Network page → node utilization |
| R03 | 0–3 hour flood nowcasting | `NowcastEngine` (9 horizons) | `services/nowcast/engine.py` | `test_endpoints.py::test_flood_nowcast` | Nowcast page → T+0 through T+180 chart |
| R04 | Flood depth estimation | XGBoost Regressor | `services/ml/predictor.py` | `test_ml_predictor.py` | Nowcast zones → `depth_cm` field |
| R05 | Flood onset timing (Flood Clock) | `FloodClock` in NowcastEngine | `services/nowcast/engine.py` | `test_endpoints.py::test_flood_clock_valid` | Flood Clock page → countdown |
| R06 | Risk classification | `RiskEngine` (5 components) | `services/risk/engine.py` | `test_risk_engine.py` | Colour-coded zones: GREEN/AMBER/RED |
| R07 | Identify vulnerable roads | Flood-aware Dijkstra | `services/routing/` | `test_routing.py`, `test_endpoints.py::test_safe_route` | Safe Routing → high-risk road segments |
| R08 | Safer route recommendation | NetworkX Dijkstra with flood weights | `services/routing/graph.py` | `test_routing.py` | Safe Routing → flood-aware vs normal route |
| R09 | Real-time GIS dashboard | React 19 + MapLibre GL JS | `frontend/src/pages/FloodMap.tsx` | `test_endpoints.py::test_flood_zones_geojson` | FloodMap with 7 live data layers |
| R10 | Decision support | `DecisionEngine` (7 NDMA categories) | `services/decisions/engine.py` | `test_endpoints.py::test_decisions_current` | Alerts & Decisions → ranked recommendations |
| R11 | Alert system | `AlertEngine` (4 IMD-aligned levels) | `services/alerts/engine.py` | `test_endpoints.py::test_alerts_list` | Alert feed in Command Center |
| R12 | Data provenance transparency | `DataProvenance` on all responses | `schemas/__init__.py` | All API tests check `data_source` | `SYNTHETIC_PROTOTYPE` on every endpoint |
| R13 | WebSocket real-time updates | `WSManager` | `ws/manager.py` | `test_integration.py` | Live 5-second tick in browser |
| R14 | REST API | FastAPI 16 routes | `app/routers/` | Full `tests/api/` suite | Swagger UI at `/api/docs` |
| R15 | Drainage capacity modelling | 30-node surcharge detection | `providers/synthetic_drainage.py` | `test_endpoints.py::test_drainage_status` | Drainage Network → red nodes |
| R16 | Physics-based hydrology | SCS-CN + Rational Method + Kirpich | `services/hydrology/engine.py` | `test_hydrology.py` | Methodology page → hydrology section |
| R17 | ML model | XGBoost + GridSearchCV | `services/ml/` | `test_ml_predictor.py` | System Health → ml_model_loaded: true |
| R18 | Reproducibility | Deterministic seeds (seed=42) | All training scripts | `test_ml_predictor.py::test_deterministic` | `train_models.py` → identical metrics every run |
| R19 | Scalability path | Provider abstraction + OSM upgrade path | `providers/__init__.py`, `REAL_DATA_UPGRADE.md` | — | REAL_DATA_UPGRADE.md |
| R20 | Docker deployment | Docker Compose 3 services | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | Docker build | `docker compose up` |
| R21 | Database persistence | PostgreSQL + PostGIS + SQLAlchemy ORM | `core/database.py`, `models/` | — | Backend startup creates 3 tables |
| R22 | Documentation | 18 comprehensive docs | `docs/` | — | All docs present |
| R23 | Testing | 74 tests (unit+API+integration) | `tests/` | `pytest tests/ -q` → 74 passed | Terminal demo |
| R24 | Flood zone generation | GeoJSON catchment polygons from nowcast | `routers/flood.py` | `test_endpoints.py::test_flood_zone_polygons` | FloodMap polygon layer |

---

## Architecture Component → SIH Requirement Mapping

| Component | Implements |
|-----------|-----------|
| `SyntheticRainfallProvider` | R01 |
| `SCS-CN HydrologyEngine` | R02, R16 |
| `SyntheticDrainageProvider` | R02, R15 |
| `NowcastEngine` | R03, R04, R05 |
| `RiskEngine` | R06 |
| `RoutingService` | R07, R08 |
| `AlertEngine` | R11 |
| `DecisionEngine` | R10 |
| `MLPredictor (XGBoost)` | R04, R17, R18 |
| `FloodMap (MapLibre)` | R09, R24 |
| `WebSocketManager` | R13 |
| `FastAPI Routers` | R14 |
| `ORM Models + Alembic` | R21 |
| `Docker Compose` | R20 |
| `DataProvenance schema` | R12 |

---

## Limitations and Non-Compliance

| Requirement | Gap | Reason | Mitigation |
|-------------|-----|--------|-----------|
| R01 | Real IMD data not connected | No IMD API key available | `SyntheticRainfallProvider` labelled `SYNTHETIC_PROTOTYPE` |
| R02 | Full pipe hydraulics not modelled | No SWMM integration | Rational Method approximation, documented in `DRAINAGE_NETWORK_SPEC.md` |
| R07 | Only 22 road nodes | OSM full graph not loaded | Upgrade path in `ROAD_NETWORK_SPEC.md` |
| R15 | 30 synthetic drainage nodes | No CMWSSB SCADA access | Labelled `SYNTHETIC_PROTOTYPE`, upgrade path documented |
| R17 | Trained on synthetic data | No historical flood observations | ML Model Card discloses this explicitly |
