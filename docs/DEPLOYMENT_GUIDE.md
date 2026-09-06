# FLOOD-X — Deployment Guide

> **Audience:** DevOps engineers, system administrators  
> **Environment:** Ubuntu 22.04 / Docker / PostgreSQL + PostGIS

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Dev)](#quick-start-dev)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Production Configuration](#production-configuration)
5. [Database Setup](#database-setup)
6. [Environment Variables Reference](#environment-variables-reference)
7. [Health Checks](#health-checks)
8. [Monitoring](#monitoring)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 10 GB | 50 GB |
| OS | Ubuntu 20.04 | Ubuntu 22.04 |
| Docker | 24.x | 25.x |
| Docker Compose | 2.x | 2.20+ |
| Python | 3.11 | 3.11+ |
| Node.js | 18 | 20 LTS |

---

## Quick Start (Dev)

```bash
# 1. Clone
git clone https://github.com/hasanhafeel24/flood-x.git
cd flood-x

# 2. Copy environment
cp .env.example .env

# 3. Install backend
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows
pip install -r backend/requirements.txt

# 4. Train ML models (required before first start)
python scripts/train_models.py

# 5. Install frontend
cd frontend && npm install && cd ..

# 6. Start backend
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Start frontend (new terminal)
cd frontend && npm run dev
```

Open: http://localhost:5173

---

## Docker Compose Deployment

### Build and Start

```bash
# Build all images
docker compose build

# Start all services (PostgreSQL + PostGIS, Backend, Frontend)
docker compose up -d

# Check service health
docker compose ps

# View logs
docker compose logs -f backend
```

### Services

| Service | Container | Port | Health Check |
|---------|-----------|------|-------------|
| PostgreSQL + PostGIS | `floodx-db` | 5432 | `pg_isready` |
| FastAPI Backend | `floodx-backend` | 8000 | `GET /api/v1/health` |
| React Frontend (nginx) | `floodx-frontend` | 3000 | HTTP 200 |

### Stop

```bash
docker compose down          # stop containers
docker compose down -v       # stop + remove volumes (data loss!)
```

---

## Production Configuration

### Required .env Changes

```env
# Security — MUST change these
SECRET_KEY=<generate: openssl rand -hex 32>
POSTGRES_PASSWORD=<strong password>

# Environment
APP_ENV=production
APP_DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://floodx:<password>@postgres:5432/floodx
DATABASE_SYNC_URL=postgresql+psycopg2://floodx:<password>@postgres:5432/floodx

# CORS — restrict to your domain
CORS_ORIGINS=https://your-domain.com

# Providers (synthetic for prototype, real for production)
RAINFALL_PROVIDER=synthetic
TERRAIN_PROVIDER=synthetic
DRAINAGE_PROVIDER=synthetic
```

### Reverse Proxy (nginx example)

```nginx
server {
    listen 80;
    server_name flood-x.yourdomain.com;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

---

## Database Setup

### With Docker (recommended)

```bash
# PostgreSQL + PostGIS starts automatically with docker compose up
# Tables are created by SQLAlchemy on first startup (development mode)

# For production — run Alembic migrations instead:
docker compose exec backend alembic -c /app/alembic.ini upgrade head
```

### Without Docker

```bash
# Install PostgreSQL + PostGIS
sudo apt install postgresql-15 postgresql-15-postgis-3

# Create database
sudo -u postgres psql -c "CREATE USER floodx WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE DATABASE floodx OWNER floodx;"
sudo -u postgres psql -d floodx -c "CREATE EXTENSION postgis;"

# Run migrations
export DATABASE_SYNC_URL=postgresql+psycopg2://floodx:password@localhost:5432/floodx
alembic -c alembic.ini upgrade head
```

### Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check current version
alembic current

# Generate new migration after model changes
alembic revision --autogenerate -m "add_real_rainfall_table"

# Rollback one step
alembic downgrade -1
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment mode |
| `APP_DEBUG` | `false` | SQLAlchemy echo |
| `APP_VERSION` | `0.1.0` | API version label |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async DB URL (FastAPI) |
| `DATABASE_SYNC_URL` | `postgresql+psycopg2://...` | Sync DB URL (Alembic) |
| `SECRET_KEY` | — | JWT signing key |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins |
| `BACKEND_HOST` | `0.0.0.0` | Uvicorn bind host |
| `BACKEND_PORT` | `8000` | Uvicorn bind port |
| `RAINFALL_PROVIDER` | `synthetic` | `synthetic` or `imd` |
| `TERRAIN_PROVIDER` | `synthetic` | `synthetic` or `file` |
| `DRAINAGE_PROVIDER` | `synthetic` | `synthetic` or `cmwssb` |
| `PILOT_CITY` | `Chennai` | City name for labels |
| `WS_BROADCAST_INTERVAL` | `5` | WebSocket tick seconds |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API base |
| `VITE_WS_URL` | `ws://localhost:8000/ws` | Frontend WebSocket URL |

---

## Health Checks

```bash
# Backend
curl http://localhost:8000/api/v1/health
# Expected: {"status": "ok", "service": "FLOOD-X API"}

# System status
curl http://localhost:8000/api/v1/system/status

# Frontend
curl http://localhost:3000
# Expected: 200 OK with HTML
```

---

## Monitoring

### Logs

```bash
# Structured JSON logs from backend (structlog)
docker compose logs -f backend | python -m json.tool

# Filter errors only
docker compose logs backend | grep '"level":"error"'
```

### Key Metrics to Watch

| Metric | Warning Threshold | Critical |
|--------|------------------|---------|
| API response time | > 500ms | > 2000ms |
| WebSocket connections | > 100 | > 500 |
| DB pool utilization | > 70% | > 90% |
| ML prediction time | > 200ms | > 1000ms |

---

## Scaling

### Horizontal Scaling (multiple backend instances)

```bash
docker compose up --scale backend=3
```

> ⚠️ WebSocket state is in-memory — add Redis pub/sub for multi-instance WS support.

### Model Caching

ML models are loaded once at startup (`ml_predictor.py`). They are held in memory for the lifetime of the process — no per-request loading overhead.

---

## Troubleshooting

### Backend fails to start

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify models exist
ls models/
# Should show: xgboost_classifier_v1.json, xgboost_regressor_v1.json, scaler_v1.pkl

# Train if missing
python scripts/train_models.py
```

### Database connection refused

```bash
# System runs without PostgreSQL — this is expected for demo:
# backend logs will show: database_unavailable_simulation_mode
# All functionality works in SYNTHETIC_SIMULATION mode
```

### WebSocket disconnects frequently

```bash
# Increase nginx proxy timeout
proxy_read_timeout 3600;
proxy_send_timeout 3600;
```

### Frontend can't reach backend

```bash
# Check CORS_ORIGINS includes frontend URL
# Check VITE_API_BASE_URL in frontend .env
```
