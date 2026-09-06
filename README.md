# FLOOD-X — AI-Powered Urban Flood Nowcasting & Decision Support

> **SIH 2026 — Problem Statement SIH26085**  
> AI-powered real-time flood prediction and emergency decision support for Chennai, India.  
> All simulation data is clearly labelled as **SYNTHETIC / SIMULATED**.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
  - [Vercel — Frontend](#vercel--frontend)
  - [Render — Backend](#render--backend)
  - [Database Setup](#database-setup)
  - [Environment Variable Checklist](#environment-variable-checklist)
  - [Production Smoke-Test Checklist](#production-smoke-test-checklist)
  - [Troubleshooting Guide](#troubleshooting-guide)
- [Project Structure](#project-structure)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      PRODUCTION                         │
│                                                         │
│   Vercel (React/Vite SPA)                               │
│        │                                                │
│        │ HTTPS REST + WSS WebSocket                     │
│        ▼                                                │
│   Render (FastAPI / Uvicorn)                            │
│        │                                                │
│        ├── PostgreSQL (Render Managed)                  │
│        ├── XGBoost ML Models (./models/)                │
│        ├── Hydrology / Drainage Engine (synthetic)      │
│        └── WebSocket Manager (real-time broadcast)      │
└─────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- Frontend and backend are independently deployed (no monolith)
- Backend degrades gracefully if PostgreSQL is unavailable (simulation mode)
- All data providers default to `synthetic` — no external API keys needed
- WebSocket uses `wss://` in production, `ws://` in development
- ML models (XGBoost JSON format) are committed to the repository

---

## Features

| Feature | Description |
|---------|-------------|
| **Flood Nowcasting** | XGBoost-based 3-hour flood probability forecast |
| **Flood Clock** | Time-to-flood countdown for monitored locations |
| **Flood Zones** | Real-time risk zone map via MapLibre GL JS |
| **Safe Routing** | Flood-aware evacuation route planning (NetworkX graph) |
| **Drainage Network** | Drainage system capacity and status monitoring |
| **Nowcast** | AI confidence-scored 3-hour rainfall prediction |
| **Decision Support** | Automated emergency response recommendations |
| **Simulation Center** | Configurable flood scenario simulation engine |
| **Real-time WebSocket** | Live data broadcast to all connected clients |
| **XAI Explainability** | SHAP-style feature importance for ML predictions |

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with PostGIS (optional — app works without it)
- Docker (optional, for database)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/flood-x.git
cd flood-x

# 2. Configure environment
cp .env.development.example .env
# Edit .env — most defaults work for local dev

# 3. Start PostgreSQL (optional — using Docker)
docker compose up -d postgres

# 4. Install backend dependencies
cd backend
python -m venv ../venv
../venv/Scripts/activate   # Windows
pip install -r requirements.txt

# 5. Run database migrations (optional)
cd ..
export DATABASE_SYNC_URL=postgresql+psycopg2://floodx:floodx_dev_password@localhost:5432/floodx
alembic upgrade head

# 6. Start backend
cd backend
python run.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/api/docs

# 7. Install and start frontend (new terminal)
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

---

## Production Deployment

### Architecture

```
GitHub Repository
      │
      ├── Vercel  (auto-deploy on push to main)
      │     └── frontend/   →  React/Vite SPA
      │
      └── Render  (auto-deploy on push to main)
            └── backend/    →  FastAPI/Uvicorn API
                  └── Managed PostgreSQL (Render)
```

---

### Vercel — Frontend

#### 1. Import Repository

1. Go to [vercel.com](https://vercel.com) → New Project → Import Git Repository
2. Select the `flood-x` repository
3. Vercel auto-detects `vercel.json` — **no framework preset needed**

#### 2. Build Settings (auto-detected from `vercel.json`)

| Setting | Value |
|---------|-------|
| Build Command | `cd frontend && npm install && npm run build` |
| Output Directory | `frontend/dist` |
| Install Command | `cd frontend && npm install` |

#### 3. Environment Variables (Vercel Dashboard → Settings → Environment Variables)

| Variable | Value | Notes |
|----------|-------|-------|
| `VITE_API_BASE_URL` | `https://flood-x-api.onrender.com` | Your Render service URL (no trailing slash) |
| `VITE_WS_URL` | `wss://flood-x-api.onrender.com/ws` | Use `wss://` for production |
| `VITE_APP_NAME` | `FLOOD-X` | |
| `VITE_APP_ENV` | `production` | |
| `VITE_MAPTILER_KEY` | *(leave empty)* | Optional — free tiles work without a key |

> **Important:** `VITE_*` variables are baked into the JS bundle at build time.  
> You must set them **before** deploying, or redeploy after setting them.  
> Never put backend secrets (DATABASE_URL, SECRET_KEY) in `VITE_*` variables.

#### 4. Deploy

Click **Deploy**. Vercel will:
1. Run `npm install && npm run build`
2. Serve the `dist/` directory as a static SPA
3. Apply SPA routing rewrites (all routes → `index.html`)

#### 5. After First Deploy

Copy your Vercel URL (e.g., `https://flood-x.vercel.app`) and set it as `CORS_ORIGINS` on the Render backend (see below).

---

### Render — Backend

#### 1. Connect Repository

1. Go to [render.com](https://render.com) → New → Blueprint
2. Select the `flood-x` repository
3. Render detects `render.yaml` automatically and creates:
   - **Web Service**: `flood-x-api`
   - **PostgreSQL**: `flood-x-db`

#### 2. Required Environment Variables

Set these in **Render Dashboard → flood-x-api → Environment**:

| Variable | Value | Notes |
|----------|-------|-------|
| `APP_ENV` | `production` | |
| `APP_DEBUG` | `false` | |
| `SECRET_KEY` | *(generate)* | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | *(from Render DB)* | Render sets this automatically via `fromDatabase` in render.yaml |
| `DATABASE_SYNC_URL` | *(from Render DB)* | Set manually — use `postgresql+psycopg2://` scheme |
| `CORS_ORIGINS` | `https://your-app.vercel.app` | Your Vercel frontend URL |
| `ML_MODELS_DIR` | `./models` | Models are in `backend/models/` |

#### 3. Auto-configured by `render.yaml`

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r backend/requirements-prod.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info` |
| Root Directory | `backend` |
| Health Check | `GET /api/v1/health` |
| Plan | Free |

#### 4. Get the `DATABASE_SYNC_URL`

1. Render Dashboard → `flood-x-db` → Connection → Internal Database URL
2. Copy the URL (starts with `postgresql://`)
3. Change the scheme: `postgresql://` → `postgresql+psycopg2://`
4. Set as `DATABASE_SYNC_URL` in the web service environment

#### 5. Deploy

Render deploys automatically. Monitor logs in **Render Dashboard → Logs**.

Expected startup output:
```
INFO     flood_x_startup version=0.1.0 env=production
INFO     database_tables_initialized
INFO     flood_x_ready host=0.0.0.0 port=10000
```

If the database is unavailable:
```
WARNING  database_unavailable_simulation_mode  mode=SYNTHETIC_SIMULATION — no persistence
INFO     flood_x_ready host=0.0.0.0 port=10000
```
This is **expected** — the API works in simulation mode without PostgreSQL.

---

### Database Setup

#### Option A: Let the App Create Tables (Simplest)

The app automatically runs `Base.metadata.create_all()` on startup. For the initial deployment, this is sufficient.

#### Option B: Run Alembic Migrations (Recommended for Production)

After deploying the database, run migrations from your local machine:

```bash
# 1. Set your Render database URL
export DATABASE_SYNC_URL="postgresql+psycopg2://floodx:PASS@RENDER_HOST:5432/floodx"

# 2. From the repo root:
alembic upgrade head

# 3. Verify
alembic current
```

#### PostGIS Extension

The free-tier Render PostgreSQL does **not** include PostGIS.  
The application's geospatial models are disabled in free-tier mode — all spatial data is computed in-memory using synthetic coordinates.

If you need PostGIS:
1. Upgrade to a paid Render PostgreSQL instance
2. Connect and run: `CREATE EXTENSION IF NOT EXISTS postgis;`
3. Re-run `alembic upgrade head`

---

### Environment Variable Checklist

#### Render Backend (Required)

- [ ] `APP_ENV=production`
- [ ] `APP_DEBUG=false`
- [ ] `SECRET_KEY` — 64-char hex string (never reuse dev value)
- [ ] `DATABASE_URL` — `postgresql+asyncpg://...` (auto-set by Render blueprint)
- [ ] `DATABASE_SYNC_URL` — `postgresql+psycopg2://...` (set manually)
- [ ] `CORS_ORIGINS` — your Vercel URL (e.g., `https://flood-x.vercel.app`)
- [ ] `ML_MODELS_DIR=./models`

#### Vercel Frontend (Required)

- [ ] `VITE_API_BASE_URL` — `https://flood-x-api.onrender.com`
- [ ] `VITE_WS_URL` — `wss://flood-x-api.onrender.com/ws`

#### Security Verification

- [ ] No `.env` file committed to repository
- [ ] `SECRET_KEY` is not the default dev value
- [ ] No backend URLs or secrets in `VITE_*` variables
- [ ] `CORS_ORIGINS` is your specific Vercel URL (not `*`)

---

### Production Smoke-Test Checklist

Run these after deployment to verify the stack:

#### Backend Health

```bash
# Health endpoint
curl https://flood-x-api.onrender.com/api/v1/health

# Expected response:
# {"status":"ok","service":"FLOOD-X","version":"0.1.0","environment":"production",...}
```

#### API Connectivity

```bash
# Rainfall
curl https://flood-x-api.onrender.com/api/v1/rainfall/current

# Flood nowcast
curl https://flood-x-api.onrender.com/api/v1/flood/nowcast

# System status
curl https://flood-x-api.onrender.com/api/v1/system/status
```

#### CORS Verification

```bash
curl -H "Origin: https://flood-x.vercel.app" \
     -I https://flood-x-api.onrender.com/api/v1/health
# Look for: Access-Control-Allow-Origin: https://flood-x.vercel.app
```

#### WebSocket

Open browser console on your Vercel app:
```javascript
// Check WebSocket connection status
// Should log: [FLOOD-X WS] Connected to wss://flood-x-api.onrender.com/ws
```

#### Frontend Checklist

- [ ] Vercel production build succeeds (no TypeScript errors)
- [ ] App loads at Vercel URL
- [ ] No CORS errors in browser console
- [ ] MapLibre map renders (OpenFreeMap tiles load)
- [ ] API calls return data (check Network tab)
- [ ] WebSocket connects (`wss://` shown in console)
- [ ] Flood simulation starts and updates
- [ ] Nowcast data displays
- [ ] Flood Clock countdown works
- [ ] Safe routing returns a path
- [ ] Alerts page loads
- [ ] Decision support page loads

#### Full Stack Feature Checklist

- [ ] Vercel production build ✓
- [ ] Render backend build ✓
- [ ] Backend health endpoint ✓
- [ ] API connectivity ✓
- [ ] CORS working ✓
- [ ] Database connection (or graceful simulation fallback) ✓
- [ ] ML model loading ✓
- [ ] WebSocket connection (wss://) ✓
- [ ] WebSocket reconnect (disable network briefly) ✓
- [ ] MapLibre renders ✓
- [ ] Flood simulation ✓
- [ ] Nowcast ✓
- [ ] Flood Clock ✓
- [ ] Flood zones ✓
- [ ] Safe routing ✓
- [ ] Decision support ✓
- [ ] Error handling (disconnect backend, verify graceful UI) ✓
- [ ] No secrets exposed in browser JS ✓

---

### Troubleshooting Guide

#### Backend Issues

**Problem: Service fails to start on Render**
```
ModuleNotFoundError: No module named 'app'
```
Solution: Ensure `rootDir: backend` is set in `render.yaml`. The `uvicorn app.main:app` command must run from within the `backend/` directory.

---

**Problem: Database connection error at startup**
```
WARNING database_unavailable_simulation_mode
```
This is **not a fatal error**. The app works in simulation mode. To enable full persistence:
1. Verify `DATABASE_URL` is set correctly in Render environment
2. Ensure the scheme is `postgresql+asyncpg://` (not `postgresql://`)
3. Render's internal database URL uses `postgresql://` by default — change the scheme

---

**Problem: CORS error in browser**
```
Access to XMLHttpRequest at 'https://flood-x-api.onrender.com/...' from origin
'https://your-app.vercel.app' has been blocked by CORS policy
```
Solution: Set `CORS_ORIGINS=https://your-app.vercel.app` in Render environment.  
Must exactly match the Vercel URL (no trailing slash, correct protocol).

---

**Problem: WebSocket connection fails**
```
[FLOOD-X WS] Error  WebSocketError
```
- Ensure `VITE_WS_URL` uses `wss://` (not `ws://`) in production
- Render supports WebSockets on all plans
- Render's free tier has a 30-second inactivity timeout — the heartbeat (10s ping) keeps connections alive

---

**Problem: ML model not found**
```
FileNotFoundError: models/xgboost_classifier_v1.json not found
```
- Verify `ML_MODELS_DIR=./models` is set in Render environment
- The models should be committed: `models/*.json` and `models/*.pkl` are tracked in git
- Check that the files exist: `git ls-files models/`

---

**Problem: Frontend shows "API Error" for all requests**
```
[FLOOD-X API Error] undefined undefined Network Error
```
- Check `VITE_API_BASE_URL` is set in Vercel environment
- Verify the Render service is running (not sleeping — free tier sleeps after 15 min)
- First request after sleep takes 30-60 seconds (Render cold start)

---

#### Free Tier Limitations

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| Render free tier sleeps after 15 min inactivity | First request is slow (30-60s cold start) | Use [UptimeRobot](https://uptimerobot.com) to ping every 5 min |
| 512 MB RAM | XGBoost + pandas uses ~200-300 MB | Should fit; monitor Render metrics |
| Free PostgreSQL expires after 90 days | Data loss | Use paid tier or export data before expiry |
| No PostGIS on free PostgreSQL | Geospatial DB features disabled | Use simulation mode (default) |

---

## Project Structure

```
flood-x/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── core/               # Config, database, logging
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── routers/            # API route handlers
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic
│   │   ├── simulation/         # Flood simulation engine
│   │   ├── providers/          # Data providers (synthetic/imd/file)
│   │   └── websocket/          # WebSocket manager
│   ├── requirements.txt        # Full dev requirements
│   ├── requirements-prod.txt   # Production requirements (no GDAL)
│   ├── Dockerfile              # Container definition
│   └── run.py                  # Local dev entry point
│
├── frontend/                   # React/Vite SPA
│   ├── src/
│   │   ├── api/                # API client (axios)
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks (useWebSocket, etc.)
│   │   ├── pages/              # Page components
│   │   └── store/              # Zustand state management
│   ├── vite.config.ts          # Vite + dev proxy config
│   └── package.json
│
├── database/
│   └── migrations/             # Alembic migrations
│
├── models/                     # Pre-trained ML models
│   ├── xgboost_classifier_v1.json
│   ├── xgboost_regressor_v1.json
│   ├── scaler_v1.pkl
│   └── training_metadata_v1.json
│
├── docs/                       # Technical documentation
├── tests/                      # Integration and unit tests
│
├── .env.example                # Environment template
├── .env.development.example    # Development environment template
├── .env.production.example     # Production environment template
├── vercel.json                 # Vercel deployment configuration
├── render.yaml                 # Render deployment configuration
├── Procfile                    # Fallback process definition
└── alembic.ini                 # Database migration configuration
```

---

## License

SIH 2026 academic project. All flood data is synthetic and for demonstration purposes only.
