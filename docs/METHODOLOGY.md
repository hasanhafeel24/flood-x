# FLOOD-X — Methodology

> Technical Methodology Documentation  
> SIH 2026 — Problem Statement SIH26085  
> AI-Powered Urban Flood Nowcasting & Decision Support System

---

## 1. System Overview

FLOOD-X implements a physics-informed, AI-augmented flood nowcasting pipeline for urban drainage areas.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLOOD-X PIPELINE                             │
│                                                                     │
│  Rainfall Input                                                     │
│  (IMD / Synthetic)                                                  │
│       │                                                             │
│       ▼                                                             │
│  SCS-CN Hydrology Engine ──────────────────────────────────────┐   │
│  - AMC-adjusted CN                                              │   │
│  - Kirpich time of concentration                                │   │
│  - Rainfall excess & peak flow (Rational Method)                │   │
│       │                                                         │   │
│       ▼                                                         │   │
│  Synthetic Drainage Network (30 nodes)                          │   │
│  - Node-level utilization                                       │   │
│  - Surcharge detection                                          │   │
│  - Bottleneck identification                                    │   │
│       │                                                         │   │
│       ▼                                                         │   │
│  XGBoost ML Predictor ──────────────────────────────────────────┤   │
│  - 14-feature flood classifier                                  │   │
│  - Flood depth regressor                                        │   │
│  - Confidence-decayed horizon predictions                       │   │
│       │                                                         │   │
│       ▼                                                         │   │
│  Nowcast Engine (T+0 to T+180 min, 9 horizons)                 │   │
│  - 70% ML + 30% physics blend                                  │   │
│  - Flood Clock (time-to-critical)                              │   │
│       │                                                         │   │
│       ▼                                                         │   │
│  Risk Engine                    Decision Support Engine         │   │
│  (5-component weighted score)   (7 action categories)          │   │
│       │                              │                          │   │
│       ▼                              ▼                          │   │
│  Alert Engine                   Safe Route Engine               │   │
│  (IMD-aligned thresholds)       (Dijkstra + flood weights)     │   │
│       │                              │                          │   │
│       └──────────────────────────────┘                          │   │
│                          │                                      │   │
│                    WebSocket Broadcast ←─────────────────────── │   │
│                          │                                       │   │
│                    React Dashboard                              │   │
│                    (11 pages, real-time)                        │   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Rainfall–Runoff Model (SCS-CN Method)

### 2.1 SCS Curve Number Method

The SCS-CN method (USDA, 1986) calculates effective rainfall (runoff) from gross rainfall using:

```
Q = (P - 0.2S)² / (P + 0.8S)     if P > 0.2S
Q = 0                              if P ≤ 0.2S

where:
  P = rainfall depth (mm)
  S = potential maximum retention = (25400/CN) - 254
  Q = runoff depth (mm)
```

### 2.2 Antecedent Moisture Condition (AMC)

CN is adjusted for antecedent soil moisture:
- **AMC-I (Dry)**: CN_I = CN_II / (2.281 - 0.01281 × CN_II)
- **AMC-II (Normal)**: CN_II = tabulated value
- **AMC-III (Wet)**: CN_III = CN_II / (0.427 + 0.00573 × CN_II)

### 2.3 Time of Concentration (Kirpich Formula)

```
Tc = 0.0195 × L^0.77 × S^(-0.385)
```

where L = catchment length (m), S = average slope (m/m)

### 2.4 Peak Flow (Rational Method)

```
Qp = (C × I × A) / 360
```

where C = runoff coefficient, I = rainfall intensity (mm/hr), A = catchment area (ha)

---

## 3. Drainage Network Model

### 3.1 Network Topology
- **30 nodes**: inlets, junctions, manholes, pumps, storage, outfalls
- **Node utilization**: Q_current / Q_capacity × 100%
- **Surcharge threshold**: utilization > 100%
- **Bottleneck**: utilization > 130%

### 3.2 Flow Routing
For this prototype, flow routing is simplified to:
- Node utilization = f(upstream runoff, drainage capacity)
- Capacities assigned from typical Chennai urban drainage literature
- Real upgrade: SWMM (EPA Storm Water Management Model) for dynamic routing

---

## 4. ML Nowcast Model

### 4.1 Model Architecture
```
Input (14 features)
    → StandardScaler (Z-normalization)
    → XGBoostClassifier (300 trees, depth=6) → P(flood ∈ {0,1})
    → XGBoostRegressor (300 trees, depth=5) [if P > 0.3] → depth (cm)
```

### 4.2 Physics-ML Blend
```
depth_final = 0.70 × depth_ML + 0.30 × depth_physics
```

Blending prevents ML outputs that violate hydrological conservation. The 70/30 split was chosen based on:
- ML: higher precision near distribution centre
- Physics: more reliable extrapolation to extreme events

### 4.3 Temporal Nowcasting (9 Horizons)
```
T+0, T+15, T+30, T+60, T+90, T+120, T+150, T+180 minutes
```

For each horizon:
- Rainfall decays with exponential `decay_factor`
- Drainage utilization propagates with lag
- ML inference runs with `horizon_minutes` as feature
- Confidence decreases with horizon (0.003/minute penalty)

---

## 5. Risk Scoring Engine

Five-component weighted scoring:

| Component | Weight | Normalisation |
|-----------|--------|---------------|
| Flood Probability | 0.30 | P(flood) ∈ [0,1] |
| Drainage Utilization | 0.25 | util_pct / 150 |
| Flood Depth | 0.20 | depth / 60 cm |
| Rainfall Intensity | 0.15 | intensity / 100 mm/hr |
| Terrain Susceptibility | 0.10 | susceptibility ∈ [0,1] |

```
risk_score = Σ(weight_i × component_i)
```

| Score | Level |
|-------|-------|
| < 0.30 | LOW |
| 0.30–0.55 | MODERATE |
| 0.55–0.80 | HIGH |
| > 0.80 | CRITICAL |

---

## 6. Flood-Aware Routing

### 6.1 Algorithm
Dijkstra's shortest path on a weighted directed graph.

### 6.2 Edge Weight Function
```
w(u,v) = travel_time × risk_multiplier + depth × 0.1

risk_multipliers:
  LOW      → 1.0  (no penalty)
  MODERATE → 2.0
  HIGH     → 5.0
  CRITICAL → 20.0 (effectively avoided)
  depth > 50cm → ∞ (impassable)
```

### 6.3 Flood Depth Estimation per Edge
```
depth_cm = (overload_factor × 0.6 + rain_factor × 0.4) × susceptibility × 60
overload_factor = max(0, drainage_util_pct - 80) / 120
rain_factor = max(0, rainfall_mm_hr - 20) / 100
```

---

## 7. Decision Support Rules

All rules are documented, threshold-based, and fully transparent:

| Rule | Trigger | Category |
|------|---------|---------|
| R1 | Intensity ≥ 35.5 mm/hr | Public Alert |
| R2 | Surcharging nodes > 0 | Drainage Ops |
| R3 | Max utilization > 130% | Pump Deploy |
| R4 | Max depth > 20 cm OR flooded zones > 2 | Road Closure |
| R5 | Risk = HIGH or CRITICAL | Emergency Pre-position |
| R6 | Max depth > 45 cm OR scenario = combined_extreme | Evacuation |
| R7 | Always | Monitoring (baseline) |

---

## 8. Alert Classification (IMD Standards)

| Severity | Rainfall Threshold | FLOOD-X Threshold |
|----------|-------------------|-------------------|
| INFO | 2.5–7.5 mm/hr | Any drainage load |
| WATCH | 7.5–35.5 mm/hr | Utilization > 80% |
| WARNING | 35.5–115.5 mm/hr | Utilization > 100% |
| EMERGENCY | > 115.5 mm/hr | Utilization > 130% |

---

## 9. Data Transparency Protocol

Every API response contains:
```json
{
  "data_source": "SYNTHETIC_PROTOTYPE",
  "provenance": {
    "source": "SYNTHETIC_PROTOTYPE",
    "model_method": "SCS-CN + XGBoost v1",
    "confidence": 0.78
  }
}
```

This ensures evaluators can never mistake synthetic model outputs for real observations.

---

## 10. References

1. USDA-SCS (1986). *Urban Hydrology for Small Watersheds*. TR-55.
2. Kirpich, Z.P. (1940). Time of concentration of small agricultural watersheds.
3. Chen, T. & Guestrin, C. (2016). XGBoost: A scalable tree boosting system.
4. IMD (2023). *Rainfall Classification Criteria*. India Meteorological Department.
5. NDMA (2020). *National Disaster Management Authority — Flood Guidelines*.
