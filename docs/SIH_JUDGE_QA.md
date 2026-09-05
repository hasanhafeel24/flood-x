# FLOOD-X — SIH Judge Q&A Preparation

> Smart India Hackathon 2026 — Problem Statement SIH26085  
> Urban Flood Nowcasting System (Drainage and Rainfall Coupling)  
> Team Preparation Document — Internal Use

---

## 1. The Killer Opening (30 seconds)

> *"Every major Indian city floods every monsoon. The problem is not the rain — it's the 30-minute warning gap between 'rainfall detected' and 'road impassable'. FLOOD-X closes that gap with an AI-powered nowcasting pipeline that goes from raw rainfall data to flood depth prediction, drainage status, safe routes, and emergency decisions — all in real time, all in one system."*

---

## 2. Anticipated Judge Questions & Model Answers

### Q1: "Is this real AI or just a dashboard with fake data?"

**Answer:**
> "Great question — this is a genuine concern with hackathon demos. Let me show you three things that prove it's real:
>
> 1. **Trained model**: We have `xgboost_classifier_v1.json` in our repository — a 300-tree XGBoost model trained on 8,000 samples. ROC-AUC: 0.998. Run `python scripts/train_models.py` right now and you'll get identical results in 2 seconds.
>
> 2. **Physics backbone**: Our hydrology engine uses the SCS-CN method — the same USDA standard used by the Central Water Commission. Every prediction comes from real equations with documented parameters.
>
> 3. **Explicit data labels**: Every API response contains `'data_source': 'SYNTHETIC_PROTOTYPE'`. We do not hide that this is synthetic data. That transparency is intentional and is itself an engineering decision."

---

### Q2: "Why synthetic data? This doesn't work on real data."

**Answer:**
> "You're right that we haven't validated on real Chennai sensor data — and we say so explicitly in our ML Model Card. But here's what matters for evaluation:
>
> The **architecture** is production-ready. Replacing synthetic inputs with real data is a configuration change, not a redesign. Specifically:
> - `providers/synthetic_rainfall.py` → replace with IMD API or AWS sensor feed
> - `services/ml/data_generator.py` → replace with historical rainfall/flood CSV  
> - Retrain with `scripts/train_models.py` → same pipeline, real data
>
> We chose synthetic data because we couldn't get IMD API access in time. The **dishonest** approach would be to use synthetic data and label it as real. We do the opposite."

---

### Q3: "What's new here? Chennai already has flood monitoring systems."

**Answer:**
> "Existing systems typically do one thing: alert when a gauge overflows. FLOOD-X does five things simultaneously:
>
> 1. **Nowcast**: Not 'is it flooding now?' but 'will it flood in 30, 60, 90 minutes?' — at specific locations
> 2. **Drainage coupling**: Links rainfall to drainage utilization to surface flooding — the full causal chain
> 3. **Flood-aware routing**: Real-time Dijkstra re-routing around flooded roads
> 4. **Decision support**: Ranked, reasoned emergency response recommendations
> 5. **Transparency**: Every prediction has a confidence score, data source, and rationale
>
> The 2015 Chennai floods caused ₹20,000 crore damage. The NDMA report identified 'lack of integrated real-time decision support' as a key gap. FLOOD-X directly addresses that gap."

---

### Q4: "Your accuracy is 97%. That seems too high."

**Answer:**
> "You're right to be sceptical. The 97% is on synthetic test data from the same distribution as training data — which is exactly what you'd expect from a well-configured model. We document this clearly in our ML Model Card.
>
> What matters more:
> - Recall on the flood class: 97% — we miss very few real flood events
> - ROC-AUC: 0.998 — excellent discrimination between flood/no-flood
> - Regressor R²: 0.9948 — but again, synthetic data
>
> For operational use, we'd expect 70–85% accuracy on real data initially, improving with more historical validation. We've designed the system so that if ML confidence is low, the system transparently falls back to physics-based (SCS-CN) predictions."

---

### Q5: "How does this scale to a real city?"

**Answer:**
> "The prototype is intentionally small (12 catchments, 30 drainage nodes, 22 road nodes) for demonstration clarity. Scaling requires:
>
> 1. **Catchments**: Chennai has ~150 sub-catchments. Same SCS-CN code, more entries in `SYNTHETIC_CATCHMENTS` list
> 2. **Drainage**: Replace 30-node synthetic network with real CMWSSB SCADA data or EPA-SWMM model export
> 3. **Road network**: `osmnx.graph_from_place('Chennai, India')` gives 50,000+ real road nodes — same Dijkstra algorithm
> 4. **ML**: Retrain on larger datasets; consider LSTM for temporal dependencies
> 5. **Infrastructure**: Docker + PostgreSQL + TimescaleDB for time-series persistence
>
> The architecture is explicitly designed with this upgrade path."

---

### Q6: "What happens when the ML model is wrong?"

**Answer:**
> "Three safety layers:
>
> 1. **Confidence scores**: Every prediction carries a confidence value (0.40–0.90). Low confidence triggers a fallback to the rule-based system.
>
> 2. **Physics blend**: Final predictions are 70% ML + 30% physics (SCS-CN). This prevents physically impossible outputs — you can't get zero depth with 100mm rainfall.
>
> 3. **Decision disclaimer**: Every recommendation includes: 'Decision-support only — not official emergency orders.' The system explicitly prohibits autonomous action.
>
> We've also written a formal ADR (Architecture Decision Record) on this: ADR-006."

---

### Q7: "Is this deployable on government infrastructure?"

**Answer:**
> "We've designed with that in mind:
>
> - **Docker Compose**: Single command `docker-compose up` — runs on any Linux server
> - **PostgreSQL + PostGIS**: Standard, auditable, government-approved stack
> - **No proprietary APIs**: All external dependencies are open-source or replaceable
> - **Offline capable**: Backend works without internet (synthetic mode) — critical for disaster scenarios when connectivity may fail
> - **API-first**: Every feature accessible via REST API — integrates with NIC/NDMA systems
>
> For production, we'd add Nginx reverse proxy, SSL termination, and Alembic database migrations (the schema is already defined)."

---

### Q8: "Show me the code. What's the most important file?"

**Answer:**
> "I'd point you to three files:
>
> 1. **`backend/app/services/nowcast/engine.py`** — the heart of the system. Physics → ML → risk → clock in one place.
>
> 2. **`backend/app/services/decisions/engine.py`** — all 7 decision rules, explicitly coded, documented, with thresholds matching NDMA and IMD standards.
>
> 3. **`scripts/train_models.py`** — run it yourself right now. It trains two XGBoost models in 2 seconds and produces documented performance metrics."

---

### Q9: "What's your SIH problem statement coverage?"

**Requirement mapping:**

| SIH26085 Requirement | FLOOD-X Implementation | Status |
|---------------------|----------------------|--------|
| Rainfall integration | `providers/synthetic_rainfall.py` + IMD threshold matching | ✅ |
| Drainage coupling | `providers/synthetic_drainage.py` + 30-node network | ✅ |
| 0–3hr nowcast | `services/nowcast/engine.py` (9 horizons) | ✅ |
| Flood depth prediction | XGBoost regressor + SCS-CN blend | ✅ |
| Time-to-flood | Flood Clock in nowcast engine | ✅ |
| Risk classification | 5-component weighted risk engine | ✅ |
| Safe routing | NetworkX Dijkstra + flood weights | ✅ |
| Alerts | IMD-aligned 4-level alert engine | ✅ |
| Decision support | 7-category decision engine | ✅ |
| Data provenance | `DataProvenance` schema on every API | ✅ |
| Real-time dashboard | 11-page React frontend + WebSocket | ✅ |
| Documentation | Methodology, ML Card, ADRs, Quickstart | ✅ |

---

## 3. Demo Script (5-Minute Judge Presentation)

### Minute 1: Problem statement
- Open `docs/METHODOLOGY.md` — show the pipeline diagram
- Key message: "Rainfall → Drainage → ML → Decision in one integrated system"

### Minute 2: Live simulation
- Go to Simulation Centre → Select "Extreme Rainfall" → Start
- Show: intensity rising, drainage nodes turning red, alerts appearing

### Minute 3: FloodMap
- Switch to FloodMap
- Show: polygon zones turning RED, drainage nodes surcharging, click Velachery
- Click "Safe Route" → show alternate path via ORR bypass

### Minute 4: Decision Support
- Go to Alerts & Decisions → Decisions tab
- Show: 6 ranked recommendations, IMMEDIATE tag on pump deployment
- Expand one card: action steps, target locations, confidence score

### Minute 5: Technical credibility
- Open Swagger UI: `localhost:8000/api/docs`
- Show `/api/v1/system/status` → `ml_model_loaded: true, ml_model_version: "v1"`
- Show `/api/v1/flood/nowcast` → live JSON with `data_source: SYNTHETIC_PROTOTYPE`
- Key message: "Every prediction is traceable, every threshold is documented, every data source is declared"

---

## 4. Common Objections & Responses

| Objection | Response |
|-----------|---------|
| "This is just a dashboard" | Show the 7 backend services, 43 unit tests, trained model files |
| "Synthetic data is cheating" | "We label it explicitly. Cheating would be not disclosing it." |
| "This doesn't help real people" | Reference 2015 Chennai floods, NDMA gap analysis |
| "The UI is too polished, not technical" | "The technical work is in the backend. Let me show you the code." |
| "XGBoost is old technology" | "For explainability and auditability in emergency management, XGBoost's interpretability beats LSTM black boxes." |

---

## 5. Scoring Rubric Self-Assessment

| Criterion | Score (est.) | Evidence |
|-----------|-------------|---------|
| Innovation | 8/10 | Physics-ML blend, flood-aware routing, decision engine |
| Technical Depth | 9/10 | 43 tests, trained models, documented ADRs |
| Feasibility | 8/10 | Docker, real-data upgrade path, OSS stack |
| Presentation | 8/10 | 11-page dashboard, live demo, Swagger UI |
| Impact | 9/10 | Chennai pilot, NDMA gap, scalable architecture |
| **Total** | **42/50** | |

---

## 6. Backup Plans

| Failure | Backup |
|---------|--------|
| Backend crashes | Pre-recorded video in `docs/` |
| Network fails | Localhost demo (no internet required) |
| DB not available | SYNTHETIC_SIMULATION mode (automatic fallback) |
| ML slow | Models pre-trained in `models/` — no retraining needed |
| Judge wants edge case | `POST /demo/start` → runs full 8-phase deterministic scenario |
