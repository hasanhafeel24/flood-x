"""
Explain router — GET /api/v1/explain/prediction
================================================
Returns per-feature XGBoost gain-weighted contributions for a prediction.

Methodology:
  contribution_i = feature_importance_i × normalized_feature_value_i
  (Approximation of SHAP marginal contributions)

DATA SOURCE: SYNTHETIC_PROTOTYPE
"""
from fastapi import APIRouter, Query
from app.services.ml.predictor import ml_predictor
from app.providers import synthetic_rainfall, synthetic_drainage

router = APIRouter()


@router.get("/explain/prediction")
async def explain_prediction(
    intensity: float = Query(None, description="Rainfall intensity mm/hr (default: current live value)"),
    accumulated: float = Query(None, description="Accumulated rainfall mm (default: current live value)"),
    utilization: float = Query(None, description="Drainage utilization % (default: current live avg)"),
    surcharging: int = Query(None, description="Surcharging nodes (default: current live count)"),
    horizon_minutes: int = Query(60, ge=0, le=180, description="Forecast horizon in minutes"),
):
    """
    Explain a flood prediction — returns per-feature contributions.

    Uses current live values if parameters not provided.
    Contributions are XGBoost gain-weighted (approximation of SHAP values).

    DATA SOURCE: SYNTHETIC_PROTOTYPE
    """
    # Use current live values as defaults
    live_intensity = synthetic_rainfall.current_intensity
    drainage_status = await synthetic_drainage.get_network_status(live_intensity)

    intensity = intensity if intensity is not None else live_intensity
    accumulated = accumulated if accumulated is not None else getattr(synthetic_rainfall, '_accumulated', intensity * 2)
    utilization = utilization if utilization is not None else drainage_status.average_utilization_pct
    surcharging = surcharging if surcharging is not None else drainage_status.surcharging_nodes

    explanation = ml_predictor.explain_prediction(
        rainfall_intensity_mm_hr=intensity,
        accumulated_rainfall_mm=accumulated,
        drainage_utilization_pct=utilization,
        drainage_surcharging_nodes=surcharging,
        catchment_imperviousness=0.65,      # Chennai urban median
        catchment_cn=82,                    # CN AMC-II urban
        terrain_elevation_m=2.0,            # Chennai low-lying median
        terrain_susceptibility=0.72,        # High susceptibility urban
        antecedent_moisture_mm=25.0,        # AMC-II antecedent
        horizon_minutes=horizon_minutes,
    )

    return {
        **explanation,
        "input_parameters": {
            "rainfall_intensity_mm_hr": intensity,
            "accumulated_rainfall_mm": accumulated,
            "drainage_utilization_pct": utilization,
            "surcharging_nodes": surcharging,
            "horizon_minutes": horizon_minutes,
        },
        "note": "Contributions computed with live sensor values as defaults",
    }


@router.get("/explain/feature-importance")
async def get_feature_importance():
    """
    Global XGBoost feature importance (gain).
    Same across all predictions — shows which features the model relies on most.

    DATA SOURCE: ML model trained on SYNTHETIC_PROTOTYPE data
    """
    if ml_predictor.is_loaded and ml_predictor._classifier is not None:
        import numpy as np
        importances = ml_predictor._classifier.feature_importances_
        from app.services.ml.predictor import FEATURE_NAMES
        human_names = {
            "rainfall_intensity_mm_hr":   "Rainfall Intensity",
            "rainfall_duration_hr":       "Rainfall Duration",
            "accumulated_rainfall_mm":    "Accumulated Rainfall",
            "drainage_utilization_pct":   "Drainage Utilization",
            "drainage_surcharging_nodes": "Surcharging Nodes",
            "catchment_imperviousness":   "Catchment Imperviousness",
            "catchment_cn":               "SCS Curve Number",
            "catchment_area_ha":          "Catchment Area",
            "terrain_elevation_m":        "Terrain Elevation",
            "terrain_slope_pct":          "Terrain Slope",
            "terrain_susceptibility":     "Terrain Susceptibility",
            "antecedent_moisture_mm":     "Antecedent Moisture",
            "time_since_last_rain_hr":    "Time Since Rain",
            "horizon_minutes":            "Forecast Horizon",
        }
        features = []
        for fname, imp in zip(FEATURE_NAMES, importances):
            features.append({
                "feature": fname,
                "label": human_names.get(fname, fname),
                "importance": round(float(imp), 4),
                "importance_pct": round(float(imp) * 100, 2),
            })
        features.sort(key=lambda x: x["importance"], reverse=True)
        for i, f in enumerate(features):
            f["rank"] = i + 1
        return {
            "features": features,
            "model_version": ml_predictor.model_version,
            "importance_type": "gain",
            "data_source": "SYNTHETIC_PROTOTYPE",
            "note": "Feature importances from XGBoost model trained on synthetic data",
        }

    # Fallback: use documented values from ML model card
    return {
        "features": [
            {"rank": 1, "feature": "rainfall_intensity_mm_hr",   "label": "Rainfall Intensity",       "importance": 0.3449, "importance_pct": 34.49},
            {"rank": 2, "feature": "accumulated_rainfall_mm",    "label": "Accumulated Rainfall",     "importance": 0.3324, "importance_pct": 33.24},
            {"rank": 3, "feature": "rainfall_duration_hr",       "label": "Rainfall Duration",        "importance": 0.0760, "importance_pct": 7.60},
            {"rank": 4, "feature": "drainage_surcharging_nodes", "label": "Surcharging Nodes",        "importance": 0.0514, "importance_pct": 5.14},
            {"rank": 5, "feature": "catchment_imperviousness",   "label": "Catchment Imperviousness", "importance": 0.0481, "importance_pct": 4.81},
            {"rank": 6, "feature": "antecedent_moisture_mm",     "label": "Antecedent Moisture",      "importance": 0.0388, "importance_pct": 3.88},
            {"rank": 7, "feature": "terrain_susceptibility",     "label": "Terrain Susceptibility",   "importance": 0.0287, "importance_pct": 2.87},
            {"rank": 8, "feature": "catchment_cn",               "label": "SCS Curve Number",         "importance": 0.0220, "importance_pct": 2.20},
            {"rank": 9, "feature": "drainage_utilization_pct",   "label": "Drainage Utilization",     "importance": 0.0197, "importance_pct": 1.97},
            {"rank":10, "feature": "terrain_elevation_m",        "label": "Terrain Elevation",        "importance": 0.0182, "importance_pct": 1.82},
        ],
        "model_version": "rule_based_fallback",
        "importance_type": "gain (documented from ML model card)",
        "data_source": "SYNTHETIC_PROTOTYPE",
    }
