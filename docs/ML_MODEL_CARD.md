# FLOOD-X — ML Model Card

> Model transparency document per SIH technical requirements  
> Required for: "Not a fake AI demo" verification

---

## Model Overview

| Field | Value |
|-------|-------|
| **Project** | FLOOD-X — AI-Powered Urban Flood Nowcasting |
| **Model Type** | XGBoost Ensemble (Classifier + Regressor) |
| **Version** | v1 |
| **Task 1** | Binary flood classification (`flood_occurred`: yes/no) |
| **Task 2** | Flood depth regression (`flood_depth_cm`) |
| **Pilot Area** | Chennai, Tamil Nadu (synthetic prototype) |
| **Training Date** | 2026-09-05 |
| **Framework** | XGBoost 3.x, scikit-learn 1.x |

---

## ⚠ Data Source Declaration

> **MANDATORY DISCLOSURE — SIH Engineering Protocol**

**ALL training data is SYNTHETIC_PROTOTYPE.**

```
Data Source: SYNTHETIC_PROTOTYPE
Generator:   backend/app/services/ml/data_generator.py
Seed:        42 (deterministic, reproducible)
Samples:     8,000
```

This model has **NOT** been trained on or validated against:
- Real IMD rainfall observation data
- Real Chennai Metrowater drainage sensor readings  
- Real historical flood depth measurements
- Real satellite flood inundation products

**Suitable for:** Prototype demonstration, architecture validation, SIH evaluation  
**NOT suitable for:** Operational flood warning, real emergency decisions

---

## Training Data Schema

### Feature Set (14 features)

| # | Feature | Unit | Source |
|---|---------|------|--------|
| 1 | `rainfall_intensity_mm_hr` | mm/hr | Synthetic — SCS-based |
| 2 | `rainfall_duration_hr` | hours | Synthetic |
| 3 | `accumulated_rainfall_mm` | mm | Synthetic |
| 4 | `drainage_utilization_pct` | % | Synthetic drainage model |
| 5 | `drainage_surcharging_nodes` | count | Synthetic drainage model |
| 6 | `catchment_imperviousness` | 0–1 | Literature CN values |
| 7 | `catchment_cn` | 25–100 | SCS Curve Number table |
| 8 | `catchment_area_ha` | ha | Synthetic (approx. Chennai) |
| 9 | `terrain_elevation_m` | m MSL | Synthetic (low-lying bias) |
| 10 | `terrain_slope_pct` | % | Synthetic |
| 11 | `terrain_susceptibility` | 0–1 | Derived from area/elevation |
| 12 | `antecedent_moisture_mm` | mm | SCS AMC model |
| 13 | `time_since_last_rain_hr` | hours | Synthetic |
| 14 | `horizon_minutes` | minutes | 0, 15, 30, 60, 90, 120, 180 |

### Target Variables

| Variable | Type | Description |
|----------|------|-------------|
| `flood_occurred` | Binary | 1 if surface flooding predicted |
| `flood_depth_cm` | Continuous | Inundation depth in cm |
| `risk_level_int` | Ordinal | 0=LOW, 1=MOD, 2=HIGH, 3=CRIT |

---

## Training Configuration

### Flood Classifier (XGBClassifier)
```yaml
n_estimators:    300
max_depth:       6
learning_rate:   0.05
subsample:       0.8
colsample_bytree: 0.8
min_child_weight: 3
scale_pos_weight: 0.109  # auto-computed from class imbalance
eval_metric:     logloss
```

### Flood Depth Regressor (XGBRegressor)
```yaml
n_estimators:    300
max_depth:       5
learning_rate:   0.05
subsample:       0.8
colsample_bytree: 0.8
min_child_weight: 3
# Trained only on flooded samples (y_class == 1)
```

---

## Evaluation Results

### Classifier (Test Set: 1,600 samples)

| Metric | Value |
|--------|-------|
| **Accuracy** | **97.38%** |
| **F1-Score** | **98.56%** |
| **ROC-AUC** | **99.79%** |
| Precision (Flood) | 1.00 |
| Recall (Flood) | 0.97 |
| Precision (No Flood) | 0.76 |
| Recall (No Flood) | 0.98 |

### Regressor (Flooded samples only: 1,180 test)

| Metric | Value |
|--------|-------|
| **MAE** | **10.64 cm** |
| **R²** | **0.9948** |

### Important Note on High Performance
> The high classifier accuracy (97.4%) reflects performance on **synthetic data generated from the same underlying distribution**. This is expected — a well-configured model should fit its training distribution. Real-world performance will likely be **significantly lower** due to:
> - Distribution shift between synthetic and observed rainfall patterns
> - Incomplete drainage model fidelity
> - Terrain representation gaps
> - Temporal dependence not captured in i.i.d. sampling

---

## Feature Importance (Top 10)

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | `rainfall_intensity_mm_hr` | 0.3449 |
| 2 | `accumulated_rainfall_mm` | 0.3324 |
| 3 | `rainfall_duration_hr` | 0.0760 |
| 4 | `drainage_surcharging_nodes` | 0.0514 |
| 5 | `catchment_imperviousness` | 0.0481 |
| 6 | `antecedent_moisture_mm` | 0.0388 |
| 7 | `terrain_susceptibility` | 0.0287 |
| 8 | `catchment_cn` | 0.0220 |
| 9 | `drainage_utilization_pct` | 0.0197 |
| 10 | `terrain_elevation_m` | 0.0182 |

**Interpretation:** Rainfall intensity and accumulation dominate, which is physically correct. Drainage state and terrain contribute secondary signal. This feature importance ordering is consistent with hydrological theory.

---

## Inference Pipeline

```
Input features (14) 
    → StandardScaler (fitted on training data)
    → XGBClassifier → P(flood) 
    → XGBRegressor [if P > 0.3] → depth_cm
    → Blend: 70% ML + 30% physics (SCS-CN)
    → NowcastHorizon (prob, depth, confidence)
```

### Confidence Estimation
```
base_confidence = 0.75 + |P - 0.5| × 0.2  # higher near boundaries = less certain
horizon_penalty = 0.003 × horizon_minutes
final_confidence = clamp(base_confidence - horizon_penalty, 0.40, 0.90)
```

---

## Limitations & Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Synthetic data distribution shift | HIGH | Label all outputs `SYNTHETIC_PROTOTYPE` |
| Class imbalance (92% flood in training) | MEDIUM | `scale_pos_weight` applied; evaluate on minority class |
| No spatial correlation | MEDIUM | Physics blend (SCS-CN) adds physical constraint |
| No temporal sequences | MEDIUM | Horizon feature provides proxy; LSTM upgrade planned |
| Overfit to seed=42 patterns | LOW | CV planned for next iteration |

---

## Real-Data Upgrade Checklist

- [ ] Obtain IMD AWS/ARG historical rainfall (min. 3 years)  
- [ ] Obtain Chennai Metrowater SCADA drainage utilization logs  
- [ ] Obtain validated flood depth survey (2015/2021 Chennai flood events)  
- [ ] Re-run `scripts/train_models.py` with real `X`, `y_class`, `y_depth`  
- [ ] Apply temporal cross-validation (not random split)  
- [ ] Evaluate recall on CRITICAL events specifically  
- [ ] SHAP explanation validation with domain expert  

---

## Files

| File | Description |
|------|-------------|
| `models/xgboost_classifier_v1.json` | Trained XGBoost Classifier |
| `models/xgboost_regressor_v1.json` | Trained XGBoost Regressor |
| `models/scaler_v1.pkl` | Fitted StandardScaler |
| `models/training_metadata_v1.json` | Full training metadata + metrics |
| `scripts/train_models.py` | Reproducible training script |
| `backend/app/services/ml/predictor.py` | Inference service |
| `backend/app/services/ml/data_generator.py` | Synthetic data generator |
