# FLOOD-X — Configuration Guide

> Complete reference for all `.env` configuration options.

---

## Setup

```bash
cp .env.example .env
# Edit .env with your values
```

---

## Application Settings

```env
# ── App ───────────────────────────────────────────────────────────────────────
APP_ENV=development           # development | production | testing
APP_VERSION=0.1.0             # Semantic version, shown in API docs
APP_DEBUG=false               # SQLAlchemy query logging (true = verbose)

# ── Server ────────────────────────────────────────────────────────────────────
BACKEND_HOST=0.0.0.0          # Uvicorn bind host
BACKEND_PORT=8000             # Uvicorn bind port

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY=dev-secret-change  # JWT signing key (use: openssl rand -hex 32)
ALGORITHM=HS256               # JWT algorithm

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
# Production: restrict to your domain only
# CORS_ORIGINS=https://flood-x.yourdomain.com
```

---

## Database Settings

```env
# ── PostgreSQL + PostGIS ──────────────────────────────────────────────────────
POSTGRES_USER=floodx
POSTGRES_PASSWORD=floodx_dev_password    # CHANGE IN PRODUCTION
POSTGRES_DB=floodx
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# ── SQLAlchemy URLs ───────────────────────────────────────────────────────────
# Async URL (FastAPI runtime)
DATABASE_URL=postgresql+asyncpg://floodx:floodx_dev_password@localhost:5432/floodx

# Sync URL (Alembic migrations only)
DATABASE_SYNC_URL=postgresql+psycopg2://floodx:floodx_dev_password@localhost:5432/floodx
```

> **Note:** Database is optional. The system operates fully in `SYNTHETIC_SIMULATION` mode
> without PostgreSQL. A graceful fallback is built into `app/main.py`.

---

## Data Provider Settings

```env
# ── Provider Selection ────────────────────────────────────────────────────────
# Values: "synthetic" (prototype) or real provider name
RAINFALL_PROVIDER=synthetic   # synthetic | imd
TERRAIN_PROVIDER=synthetic    # synthetic | file
DRAINAGE_PROVIDER=synthetic   # synthetic | cmwssb

# ── Pilot Configuration ───────────────────────────────────────────────────────
PILOT_CITY=Chennai
PILOT_CATCHMENTS=12           # Number of catchment zones
PILOT_DRAINAGE_NODES=30       # Number of drainage nodes
```

---

## Real Data Provider Settings (production)

```env
# ── IMD Rainfall API ─────────────────────────────────────────────────────────
IMD_API_KEY=your_imd_api_key_here
IMD_STATION_ID=43279          # Chennai Airport AWS station

# ── CMWSSB Drainage SCADA ─────────────────────────────────────────────────────
CMWSSB_API_URL=http://scada.cmwssb.gov.in/api/v1
CMWSSB_TOKEN=your_token_here

# ── Terrain / DEM File Paths ──────────────────────────────────────────────────
DEM_FILE_PATH=data/terrain/chennai_dem_30m.tif
SLOPE_FILE_PATH=data/terrain/chennai_slope.tif
```

---

## ML Model Settings

```env
# ── Model Paths ───────────────────────────────────────────────────────────────
ML_MODEL_DIR=models                          # Directory containing model files
ML_CLASSIFIER_FILE=xgboost_classifier_v1.json
ML_REGRESSOR_FILE=xgboost_regressor_v1.json
ML_SCALER_FILE=scaler_v1.pkl
ML_MODEL_VERSION=v1

# ── Prediction Thresholds ─────────────────────────────────────────────────────
FLOOD_PROB_THRESHOLD_MODERATE=0.35
FLOOD_PROB_THRESHOLD_HIGH=0.60
FLOOD_PROB_THRESHOLD_CRITICAL=0.80
```

---

## WebSocket Settings

```env
# ── WebSocket Broadcast ───────────────────────────────────────────────────────
WS_BROADCAST_INTERVAL=5       # Seconds between simulation ticks
WS_MAX_CONNECTIONS=100        # Max concurrent WebSocket clients
```

---

## Frontend Settings (Vite)

```env
# ── Frontend Environment (.env in /frontend or passed as build args) ──────────
VITE_API_BASE_URL=http://localhost:8000   # Backend URL
VITE_WS_URL=ws://localhost:8000/ws       # WebSocket URL
VITE_APP_NAME=FLOOD-X
VITE_APP_ENV=development
```

---

## Environment Presets

### Minimal (no database, no real APIs)
```env
APP_ENV=development
RAINFALL_PROVIDER=synthetic
TERRAIN_PROVIDER=synthetic
DRAINAGE_PROVIDER=synthetic
```
Backend starts in `SYNTHETIC_SIMULATION` mode with all features working.

### Docker Compose
All variables are pre-configured in `docker-compose.yml` with sensible defaults.
Override by creating a `.env` file in the project root before running `docker compose up`.

### Production
```env
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=<generated>
POSTGRES_PASSWORD=<strong>
CORS_ORIGINS=https://your-domain.com
RAINFALL_PROVIDER=imd
IMD_API_KEY=<key>
```
