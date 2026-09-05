# FLOOD-X — Project Audit Report (M0)

**Project:** AI-Powered Urban Flood Nowcasting & Decision Support System  
**Target:** Smart India Hackathon 2026 — SIH26085  
**Audit Date:** 2026-09-05  
**Auditor:** Lead Software Architect / Technical Product Manager  
**Audit Type:** Greenfield (empty repository, fresh environment)

---

## 1. Repository State

| Item | Status |
|---|---|
| Repository | Initialized (empty, 0 commits) |
| Existing source code | **NONE** |
| Existing documentation | **NONE** |
| Existing tests | **NONE** |
| Existing Docker configuration | **NONE** |
| Existing CI/CD | **NONE** |
| Existing database | **NONE** |
| Existing datasets | **NONE** |

**Conclusion:** Fully greenfield project. No existing code to preserve, audit for breakage, or risk overwriting.

---

## 2. Local Development Environment

### 2.1 Runtimes Available

| Runtime | Version | Status |
|---|---|---|
| Python | 3.14.2 (CPython, system install) | ✅ Available |
| pip | 25.3 | ✅ Available |
| Node.js | 24.16.0 (LTS) | ✅ Available |
| npm | 11.13.0 | ✅ Available |
| Git | 2.51.0.windows.2 | ✅ Available |
| Docker | 29.7.2 | ✅ Available |
| Docker Compose | v5.5.0 | ✅ Available |

### 2.2 Python Packages Installed

| Package | Status |
|---|---|
| pip 25.3 | ✅ Installed |
| FastAPI / Uvicorn | ❌ Not installed — install in M1 |
| SQLAlchemy / Alembic | ❌ Not installed — install in M1 |
| Pydantic | ❌ Not installed — install in M1 |
| GeoPandas / Shapely / Rasterio | ❌ Not installed — install in M1 |
| NumPy / SciPy / Pandas | ❌ Not installed — install in M1 |
| NetworkX | ❌ Not installed — install in M1 |
| scikit-learn / XGBoost | ❌ Not installed — install in M1 |
| Psycopg2 | ❌ Not installed — install in M1 |

> ⚠️ **Python 3.14.2 Compatibility Risk:** Geospatial packages (rasterio, geopandas, GDAL) historically lag behind the latest CPython release. The Docker backend will use Python 3.11 (stable geo support). Local development will attempt Python 3.14; if incompatible, Docker-only workflow will be used and documented.

### 2.3 Node.js Global Packages
No global npm packages installed. Frontend will use `npx` (no global installs required).

---

## 3. Existing Features Audit

### A. What Already Works
**NOTHING** — repository is empty.

### B. What Partially Works
**NOTHING** — no code exists.

### C. What Is Broken
**NOTHING** — no code to break.

### D. What Is Missing (All of it)
Every component of the system must be built from scratch:

- Project foundation (venv, package.json, .gitignore, .env.example)
- FastAPI backend with all service layers
- PostgreSQL/PostGIS database with migrations
- Data provider abstraction layer + synthetic datasets
- Geospatial engine (DEM → catchments → susceptibility)
- Drainage graph engine (NetworkX)
- Hydrology/runoff engine (SCS-CN + Rational Method)
- Hydraulic/drainage state engine
- AI/ML pipeline (feature engineering → training → inference)
- 0–3 hour Nowcast engine
- Flood Clock feature
- Flood Risk engine
- Flood-aware routing engine
- Decision Support engine
- Real-time WebSocket event system
- Scenario engine (8 scenarios)
- React/TypeScript frontend (11 screens)
- MapLibre GL JS map component
- Docker Compose deployment
- Full test suite (unit, API, integration, e2e)
- 19-document documentation suite
- SIH presentation material (pitch, PPT, judge Q&A, demo script)
- Demo mode (deterministic scenario)

### E. What Should Be Redesigned
N/A — greenfield.

### F. What Should Be Preserved
N/A — greenfield.

---

## 4. Architecture Decisions

### 4.1 Overall Pattern
**Modular Monorepo with Service Boundaries**

- Docker Compose: 3 services (frontend, backend, database)
- Backend: FastAPI monolith with internal service layer (simpler than microservices for SIH demo)
- ML/simulation: In-process with backend (no separate service needed at prototype scale)
- WebSockets: Native FastAPI WebSocket support

### 4.2 Backend Layer Map

```
backend/
├── app/
│   ├── main.py                — FastAPI app factory
│   ├── routers/               — REST endpoints (/api/v1/...)
│   ├── services/
│   │   ├── rainfall/          — Rainfall ingestion + providers
│   │   ├── terrain/           — Geospatial engine
│   │   ├── drainage/          — Drainage graph engine
│   │   ├── hydrology/         — Runoff calculation
│   │   ├── hydraulic/         — Drainage state model
│   │   ├── ml/                — ML inference pipeline
│   │   ├── nowcast/           — 0-3h nowcast engine
│   │   ├── flood_clock/       — Flood Clock feature
│   │   ├── risk/              — Risk scoring engine
│   │   ├── routing/           — Flood-aware routing
│   │   ├── alerts/            — Alert generation
│   │   └── decision/          — Decision support engine
│   ├── providers/             — Data provider abstractions
│   ├── models/                — SQLAlchemy ORM models
│   ├── schemas/               — Pydantic request/response schemas
│   ├── simulation/            — Scenario engine + event loop
│   ├── websocket/             — WebSocket connection manager
│   └── core/                  — Config, DB, logging, security
├── tests/                     — Backend tests
├── requirements.txt
└── Dockerfile
```

### 4.3 Frontend Layer Map

```
frontend/
├── src/
│   ├── pages/                 — 11 route-based screens
│   ├── components/
│   │   ├── map/               — MapLibre GL JS + layers
│   │   ├── charts/            — Recharts
│   │   ├── cards/             — KPI, alert, status cards
│   │   └── common/            — Shared UI primitives
│   ├── hooks/                 — Custom hooks (WebSocket, API)
│   ├── store/                 — Zustand state
│   ├── api/                   — Typed API client
│   ├── types/                 — TypeScript definitions
│   └── utils/                 — Helpers
├── package.json
├── vite.config.ts
├── tailwind.config.ts
└── Dockerfile
```

---

## 5. Technology Stack (Final)

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React 19 + TypeScript 5 + Vite 6 | Modern, fast, type-safe |
| Styling | Tailwind CSS 3 | Design system, consistent tokens |
| Map | MapLibre GL JS 4 | Open-source WebGL maps, GeoJSON |
| Charts | Recharts 2 | React-native, composable |
| State | Zustand 5 | Lightweight, minimal boilerplate |
| HTTP | Axios 1 | Typed interceptors |
| Backend | FastAPI 0.115 + Uvicorn | Async, OpenAPI, WebSocket |
| ORM | SQLAlchemy 2 + Alembic | Async, migrations |
| Validation | Pydantic 2 | Fast, type-safe |
| Database | PostgreSQL 16 + PostGIS 3.4 | Spatial queries, reliability |
| Geo (vector) | GeoPandas + Shapely | Vector processing |
| Geo (raster) | Rasterio | DEM processing |
| Graph | NetworkX 3 | Drainage graph traversal |
| ML | scikit-learn + XGBoost | Explainable, proven |
| Numerical | NumPy + SciPy + Pandas | Scientific computing |
| DevOps | Docker 29 + Compose v5 | Reproducible deployment |

---

## 6. Data Strategy

### 6.1 Real Data (Public, Available)

| Dataset | Source | Usage |
|---|---|---|
| SRTM DEM (30m) | NASA/USGS | Terrain, slope, flow direction |
| OpenStreetMap roads | OSM/Geofabrik | Road network (Chennai) |
| LULC/Imperviousness | ISRO Bhuvan | Land cover classification |

### 6.2 Synthetic Data (Clearly Labelled)

| Dataset | Why Synthetic | Label |
|---|---|---|
| Municipal drainage network | Proprietary — unavailable | SYNTHETIC_PROTOTYPE |
| Real-time sensor readings | No sensor API access | SIMULATED |
| Historical flood events | Not publicly geolocated | SYNTHETIC_PROTOTYPE |
| Drainage pipe attributes | Municipal infrastructure | SYNTHETIC_PROTOTYPE |
| IMD real-time rainfall | Requires institutional key | SIMULATED |

**Every synthetic dataset will carry:**
```json
{
  "data_source": "SYNTHETIC_PROTOTYPE",
  "description": "Prototype dataset — not real municipal data",
  "generated_by": "FLOOD-X synthetic data generator",
  "version": "1.0"
}
```

### 6.3 Provider Abstraction

```python
class RainfallProvider(ABC):
    async def get_current(self) -> RainfallObservation: ...
    async def get_forecast(self, hours: int) -> List[RainfallForecast]: ...

class SyntheticRainfallProvider(RainfallProvider): ...  # Default
class FileRainfallProvider(RainfallProvider): ...        # Load from disk
# class IMDRainfallProvider(RainfallProvider): ...      # Stub (requires API key)
```

---

## 7. ML Model Strategy

**Primary Model: XGBoost (Classifier + Regressor)**
- Flood probability (classification)
- Estimated flood depth (regression)
- Feature importance for explainability

**Comparison Models:**
- DummyClassifier (baseline)
- Logistic Regression (linear baseline)
- Random Forest (ensemble baseline)

**Training Data:** Synthetic dataset generated from hydrological simulation outputs (physically consistent labels, not fabricated). Metrics computed on actual held-out split.

**No deep learning:** Not justified for prototype-scale synthetic data.

---

## 8. Hydrology Model Selection

**Selected: SCS Curve Number + Rational Method**

| Method | Usage | Justification |
|---|---|---|
| SCS-CN | Rainfall-to-runoff volume | Standard Indian urban hydrology practice |
| Rational Method | Peak flow estimation | Simple, defensible, widely used |
| Kirpich formula | Time of concentration | Standard approximation |
| Linear reservoir | Channel routing | Simplified routing for prototype |

All assumptions explicitly documented in `docs/HYDROLOGY_MODEL.md`.
SWMM integration path documented for production upgrade.

---

## 9. Critical Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Python 3.14 geo package incompatibility | High | Docker backend with Python 3.11; tested at M1 |
| No real drainage data | Medium | Synthetic prototype; clear labelling |
| No real-time rainfall API | Medium | Simulation provider; IMD stub ready |
| Map tiles (MapLibre needs tile source) | Medium | OpenFreeMap / CARTO free tiles |
| ML trained on synthetic data only | Medium | Clearly documented; metrics are real |

---

## 10. Missing SIH Requirements (All — Greenfield)

| Requirement | Priority |
|---|---|
| Rainfall ingestion + preprocessing | Critical |
| Terrain analysis + flow modelling | Critical |
| Drainage network representation | Critical |
| AI/ML flood prediction | Critical |
| 0–3h nowcasting | Critical |
| Flood Clock | High |
| Flood risk map | Critical |
| Flood-aware routing | High |
| Emergency alerts | High |
| Decision support | High |
| Real-time WebSocket dashboard | Critical |
| Simulation / scenario mode | Critical |
| Data provenance UI | High |
| Confidence reporting | High |
| Docker deployment | Medium |
| Full test suite | Medium |
| 19-document documentation | Medium |
| SIH presentation material | High |
| Demo mode | High |

---

## 11. Complete Milestone Roadmap

| Milestone | Description | Dependencies |
|---|---|---|
| **M0** | Project Audit *(complete)* | — |
| **M1** | Foundation: venv, Vite, Docker, .gitignore, README | M0 |
| **M2** | Data providers + synthetic datasets | M1 |
| **M3** | Geospatial engine (DEM → catchments) | M2 |
| **M4** | Database + ORM + migrations + seed | M2 |
| **M5** | Drainage graph engine (NetworkX) | M2, M4 |
| **M6** | Hydrology/runoff engine (SCS-CN) | M2, M5 |
| **M7** | Hydraulic/drainage state engine | M5, M6 |
| **M8** | AI/ML pipeline (train → evaluate → serialize) | M6, M7 |
| **M9** | 0–3h Nowcast engine | M8 |
| **M10** | Flood Clock | M9 |
| **M11** | Flood Risk engine | M9 |
| **M12** | Flood-aware routing | M11 |
| **M13** | Decision support engine | M11, M12 |
| **M14** | Backend REST APIs (all endpoints) | M9–M13 |
| **M15** | Real-time WebSocket system + scenario engine | M14 |
| **M16** | Frontend Command Center (main dashboard) | M14, M15 |
| **M17** | All 10 additional dashboard screens | M16 |
| **M18** | Full frontend ↔ backend integration | M16, M17 |
| **M19** | Full test suite (unit + API + integration + e2e) | M18 |
| **M20** | Performance profiling + optimization | M19 |
| **M21** | Docker + Compose finalization | M18 |
| **M22** | Security audit | M21 |
| **M23** | Demo mode (deterministic scenario) | M18 |
| **M24** | SIH presentation package (pitch, PPT, Q&A, script) | M23 |
| **M25** | Final end-to-end acceptance test | M24 |

---

## 12. Pre-Implementation Technical Debt

| ID | Item | Priority | When |
|---|---|---|---|
| TD-001 | Python 3.14 geo package compatibility unverified | High | M1 |
| TD-002 | No real-time IMD rainfall API | High | M2 |
| TD-003 | No municipal drainage network data | High | M2 |
| TD-004 | SWMM not integrated (prototype only) | Medium | Documented M12 |
| TD-005 | ML trained on synthetic data | Medium | Documented M8 |
| TD-006 | No satellite real-time imagery | Low | Documented M3 |

---

## 13. Audit Conclusion

**Status: GREENFIELD — ALL CLEAR TO BUILD**

- Environment: ✅ All runtimes available
- Code: ✅ Nothing to preserve or risk breaking
- Architecture: ✅ Decided (FastAPI + React + PostgreSQL/PostGIS + XGBoost)
- Data strategy: ✅ Synthetic prototype + provider abstraction
- Risks: ✅ Identified and mitigated
- Roadmap: ✅ 25 milestones defined

**Awaiting approval to begin M1: Project Foundation.**
