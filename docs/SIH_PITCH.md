# FLOOD-X
## AI-Powered Urban Flood Nowcasting & Decision Support System

**Smart India Hackathon 2026 | Problem Statement SIH26085**  
**Urban Flood Nowcasting System — Drainage and Rainfall Coupling**

---

## The Problem

India loses **₹40,000+ crore annually** to urban flooding.  
The 2015 Chennai floods: **~500 lives lost, ₹20,000 crore damage.**

**The 30-minute gap** — the time between rainfall detection and road impassability — is where lives are saved or lost.

Current systems tell you: *"It's flooding."*  
FLOOD-X tells you: *"It will flood here in 25 minutes. Take this route. Do these 6 things now."*

---

## What FLOOD-X Does

```
Rainfall Input
    ↓
SCS-CN Hydrology        (Physics-grounded runoff calculation)
    ↓
Drainage Network        (30-node utilization & surcharge detection)
    ↓
XGBoost ML Predictor   (Classifier: 97.4% accuracy | Regressor: R²=0.995)
    ↓
0–3 Hour Nowcast        (9 time horizons | Flood Clock | Depth map)
    ↓
Risk Engine            (5-component weighted transparency score)
    ↓
Safe Route             (Flood-aware Dijkstra — reroutes around flooded roads)
    ↓
Decision Support       (7 ranked action categories | NDMA-aligned thresholds)
    ↓
Emergency Dashboard    (11-page React UI | Real-time WebSocket | MapLibre)
```

---

## Key Technical Features

| Feature | Implementation |
|---------|---------------|
| **Physics backbone** | SCS-CN, AMC adjustment, Kirpich Tc, Rational Method |
| **ML models** | XGBoost Classifier + Regressor (14 features, 8000 samples) |
| **Nowcast engine** | 9 horizons T+0 → T+180min, confidence decay |
| **Flood Clock** | Time-to-critical prediction per location |
| **Safe routing** | NetworkX Dijkstra + flood-weight edge penalties |
| **Decision support** | 7 categories, ranked by urgency, with rationale |
| **Real-time** | WebSocket broadcast every 5 seconds |
| **Transparency** | Every prediction: data_source + confidence + provenance |
| **Tests** | 43 unit tests, 0 failing |

---

## Transparency Commitment

> Every API response includes `"data_source": "SYNTHETIC_PROTOTYPE"`  
> No real data is claimed where synthetic data was used.  
> This is not a limitation — it's an engineering principle.

**Real-data upgrade path:** Documented in `docs/ML_MODEL_CARD.md` and `docs/ARCHITECTURE_DECISIONS.md`

---

## Technical Stack

**Backend:** Python 3.11 · FastAPI · XGBoost · NetworkX · SCS-CN · SQLAlchemy · structlog  
**Frontend:** React 19 · TypeScript · Zustand · MapLibre GL JS · Recharts  
**Infrastructure:** Docker Compose · PostgreSQL + PostGIS · WebSocket  
**Tests:** pytest · 43 tests · 0 failures  

---

## Demo

```bash
# 1. Train models (2 seconds)
python scripts/train_models.py

# 2. Start backend
cd backend && uvicorn app.main:app --reload

# 3. Start frontend
cd frontend && npm run dev

# 4. Run deterministic demo scenario
curl -X POST localhost:8000/api/v1/demo/start
```

---

## Pilot Area: Chennai, Tamil Nadu

12 synthetic catchments · 30 drainage nodes · 22 road nodes  
Coordinates aligned to real Chennai geography (SYNTHETIC_PROTOTYPE)

**Real deployment path:**  
`osmnx.graph_from_place("Chennai, India")` → 50,000+ real road nodes  
IMD API → real rainfall · CMWSSB SCADA → real drainage

---

*"The architecture is real. The physics is real. The ML is real.*  
*The data is synthetic — and we say so on every endpoint."*
