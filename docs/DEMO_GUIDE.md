# FLOOD-X — Demo Guide

> Step-by-step guide for the SIH 2026 judge demonstration.  
> Designed for a 5-minute presentation slot.

---

## Prerequisites

Two terminals open. Both commands ready to copy-paste.

### Terminal 1 — Backend
```powershell
cd h:\flood-x\backend
h:\flood-x\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
```

### Terminal 2 — Frontend
```powershell
cd h:\flood-x\frontend
npm run dev
```

### Browser tabs (open before demo)
- Tab 1: **http://localhost:5173** (dashboard)
- Tab 2: **http://localhost:8000/api/docs** (Swagger — for technical credibility)

---

## Verify Before Starting

Check sidebar shows: **LIVE** (green) in top-left  
Check header shows: rainfall gauge reading

If backend not connected → sidebar shows DISCONNECTED (red)

---

## Phase 1 — Problem Statement (0:00–0:45)

**What to do:** Stay on Command Center (first page)

**Show:**
- Risk grid (all GREEN initially) → *"This is the resting state"*
- Rainfall gauge showing 0–4 mm/hr → *"Light morning drizzle"*
- System status footer: `SYNTHETIC_SIMULATION` badge

**Say:**
> *"Every major Indian city floods every monsoon. The problem isn't the rain — it's the 30-minute warning gap. FLOOD-X closes that gap. What you see is the operational command centre for an urban flood nowcasting system."*

---

## Phase 2 — Start the Flood Event (0:45–1:30)

**What to do:**
1. Click **Simulation** in sidebar
2. Click **Extreme Rainfall** card (120 mm/hr peak, CRITICAL)
3. Set speed to **3×**
4. Click **Start Simulation**

**Watch happen:**
- Header: rainfall gauge rises rapidly
- Sidebar: state changes from LIVE → SIMULATION
- Alerts feed starts populating (bottom-left, if visible)

**Say:**
> *"I've started the 'Extreme Rainfall' scenario — modelled on the November 2015 Chennai event. The system is running our SCS-CN hydrology model in real time: rainfall → runoff → drainage loading → ML prediction → risk score — every 5 seconds."*

---

## Phase 3 — FloodMap (1:30–2:15)

**What to do:**
1. Click **Live Flood Map** in sidebar
2. The map shows Chennai with coloured zones
3. Click on a RED/ORANGE zone → popup appears
4. Point to the drainage node layer (red circles)

**Show:**
- Polygon zones turning red (risk = HIGH/CRITICAL)
- Popup: `depth_cm`, `flood_probability`, `risk_level`
- Drainage nodes showing surcharge

**Say:**
> *"Each polygon is a catchment zone. The colour comes from our XGBoost classifier — the probability of flooding in the next 60 minutes. Green is under 35%, red is over 80%. Every value originates from the backend model — nothing is hardcoded."*

---

## Phase 4 — Nowcast & Flood Clock (2:15–2:45)

**What to do:**
1. Click **Nowcast 0–3h** in sidebar
2. Show the timeline chart — 9 horizons
3. Click **Flood Clock** in sidebar

**Show:**
- Nowcast: probability rising over T+30, T+60, T+90
- Flood Clock: countdown showing "T-XX min to WARNING"
- Status badge: WARNING or CRITICAL

**Say:**
> *"This is the core product — not 'is it flooding now', but 'will it flood in 30, 60, 90 minutes'. The Flood Clock computes the time to WARNING/CRITICAL threshold dynamically from model output."*

---

## Phase 5 — Safe Routing (2:45–3:15)

**What to do:**
1. Click **Safe Routing** in sidebar
2. Routes are auto-calculated from current flood state
3. Show the two route comparison cards

**Show:**
- Flood-aware route: avoids HIGH/CRITICAL zones
- Normal route: shorter distance, higher flood depth
- Delta: `+X min travel time, -Y cm max depth`

**Say:**
> *"This is NetworkX Dijkstra with flood-risk weights on every road edge. CRITICAL zones get a 10× travel time penalty — effectively removing them. The system returns both routes so the EOC operator can decide."*

---

## Phase 6 — Decision Support (3:15–4:00)

**What to do:**
1. Click **Alerts** in sidebar
2. Click the **Decisions** tab
3. Expand the IMMEDIATE-priority recommendation
4. Scroll to show the disclaimer at the bottom

**Show:**
- Ranked list: IMMEDIATE → HIGH → MODERATE
- Expanded card: title, rationale, action_steps, deadline_minutes, confidence
- Disclaimer: "DECISION-SUPPORT ONLY — not official emergency orders"

**Say:**
> *"Seven decision categories aligned with NDMA emergency protocols. Every recommendation has documented rationale, a confidence score, and this disclaimer — the system explicitly prohibits autonomous action. This is about augmenting human decision-making, not replacing it."*

---

## Phase 7 — Technical Credibility (4:00–4:45)

**What to do:** Switch to Tab 2 (Swagger UI at `localhost:8000/api/docs`)

1. Click `GET /api/v1/system/status` → Execute
2. Point to: `ml_model_loaded: true`, `ml_model_version: "v1"`, `data_mode: SYNTHETIC_SIMULATION`
3. Click `GET /api/v1/flood/nowcast` → Execute  
4. Point to: `data_source: SYNTHETIC_PROTOTYPE` on every nested field

**Say:**
> *"Every single response carries a `data_source` field. Synthetic data is labelled on every endpoint, on every field. Nothing is hidden — that transparency is itself an engineering decision."*

---

## Phase 8 — Live Test Run (4:45–5:00)

**What to do:** Switch to Terminal 1

```powershell
cd h:\flood-x
h:\flood-x\venv\Scripts\python.exe -m pytest tests/ -q
```

**Expected output:**
```
74 passed in 6.50s
```

**Say:**
> *"74 tests — unit tests for the hydrology engine, ML predictor, risk scoring, and routing — plus API tests hitting every endpoint and integration tests for the simulation lifecycle. All passing. This is a working engineering system, not a demo façade."*

---

## Emergency Fallback Plan

| Problem | Recovery |
|---------|----------|
| Backend crashes during demo | `cd h:\flood-x\backend && h:\flood-x\venv\Scripts\uvicorn.exe app.main:app --port 8000` (30s) |
| Frontend blank screen | Hard refresh (Ctrl+Shift+R) |
| Map doesn't load | Wait 5s for tile cache — show another page meanwhile |
| Database error in logs | Ignore — runs fine without PostgreSQL (SYNTHETIC mode) |
| WebSocket STALE warning | Refresh browser — reconnects automatically |
| Judge wants to run training | `python scripts/train_models.py` → 2 seconds, prints metrics |

---

## Questions Judges Always Ask

| Question | Answer |
|----------|--------|
| "Is this real AI?" | "Run `scripts/train_models.py` — trains in 2 seconds, prints real metrics" |
| "Why synthetic data?" | "We label it on every API response. The dishonest approach is not disclosing it." |
| "97% accuracy is too high" | "Synthetic test split — expected. Documented in ML Model Card. Real-world 70–85%." |
| "What if the model is wrong?" | "Three safety layers: confidence decay, physics blend, DECISION-SUPPORT disclaimer" |
| "Can it scale?" | "OSM gives 50k road nodes, CMWSSB gives real drainage — architecture unchanged" |
| "Show me the most important code" | `backend/app/services/nowcast/engine.py` — the complete pipeline in one file |
