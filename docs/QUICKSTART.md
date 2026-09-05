# FLOOD-X — Quick Start Guide

> Get the system running in < 5 minutes for SIH demo

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

> PostgreSQL is **optional** — system runs in SYNTHETIC_SIMULATION mode without it.

---

## 1. Clone & Setup

```bash
git clone https://github.com/hasanhafeel24/flood-x.git
cd flood-x
```

### Backend
```bash
cd backend
python -m venv ..\venv
..\venv\Scripts\activate          # Windows
# source ../venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

---

## 2. Train ML Models

```bash
# From project root, with venv active:
python scripts/train_models.py
```

Output:
```
TRAINING COMPLETE
  Classifier — Accuracy: 0.9738  F1: 0.9856  AUC: 0.9979
  Regressor  — MAE: 10.64 cm  R²: 0.9948
Models in: H:\flood-x\models
```

---

## 3. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify at: http://localhost:8000/api/v1/health

Expected response:
```json
{"status": "ok", "service": "FLOOD-X API"}
```

---

## 4. Start Frontend

```bash
cd frontend
npm run dev
```

Open: http://localhost:5173

---

## 5. Run Demo Scenario

1. Open the dashboard at http://localhost:5173
2. Navigate to **Simulation Centre**
3. Select scenario: **"Extreme Rainfall — Chennai 2015"**
4. Click **Start Simulation**
5. Watch real-time nowcasts, alerts, and decision recommendations

### Key Pages to Demonstrate

| Page | What to Show |
|------|-------------|
| **Simulation Centre** | Scenario selection, real-time controls |
| **Flood Map** | 7-layer MapLibre map with live risk zones |
| **Nowcast** | T+0 to T+3hr ML probability timeline |
| **Flood Clock** | Time-to-critical countdown |
| **Safe Routing** | Flood-aware Dijkstra route vs normal |
| **Alerts & Decisions** | Ranked emergency recommendations |
| **Drainage Network** | 30-node utilization heatmap |
| **Data Confidence** | Transparency — synthetic data labels |

---

## 6. Run Tests

```bash
# From project root, venv active:
python -m pytest tests/unit/ -v
```

Expected: **43 passed**

---

## 7. Docker (Optional)

```bash
docker-compose up -d
```

Services:
- `postgres:15` with PostGIS at port 5432
- Backend at port 8000
- Frontend at port 5173 (in dev mode)

---

## Environment Variables

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

Key settings:
```env
APP_ENV=development
RAINFALL_PROVIDER=synthetic
TERRAIN_PROVIDER=synthetic
DRAINAGE_PROVIDER=synthetic
```

---

## API Documentation

Interactive Swagger UI: http://localhost:8000/api/docs  
ReDoc: http://localhost:8000/api/redoc

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/flood/nowcast` | 0–3hr ML predictions |
| `GET /api/v1/flood/zones` | GeoJSON flood risk zones |
| `GET /api/v1/flood/zones/polygons` | GeoJSON catchment polygons |
| `GET /api/v1/drainage/status` | Live drainage network |
| `GET /api/v1/decisions/current` | Decision recommendations |
| `GET /api/v1/routes/safe` | Flood-aware route |
| `GET /api/v1/system/status` | ML model status |
| `WS  /ws` | Real-time simulation stream |

---

## Troubleshooting

### Backend won't start
```bash
# Verify Python path
python -c "import sys; print(sys.path)"
# Make sure you're in /backend and venv is active
```

### ML models missing
```bash
python scripts/train_models.py
# Models will appear in models/
```

### Frontend build fails
```bash
cd frontend
npm install  # reinstall deps
npm run build
```

### Database not connected (OK for demo)
Backend will log:
```
database_unavailable_simulation_mode
```
This is **normal** — system runs fully in SYNTHETIC_SIMULATION mode.
