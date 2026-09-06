"""
FLOOD-X ML Predictor — Inference Service
==========================================
Loads trained XGBoost models and provides flood prediction inference.

DATA SOURCE: SYNTHETIC_PROTOTYPE (model trained on synthetic data)
MODELS: xgboost_classifier_v1 + xgboost_regressor_v1

IMPORTANT: Model trained on synthetic data only.
NOT validated against real Chennai flood events.
Confidence reflects model uncertainty, not ground truth accuracy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

import numpy as np
import structlog

log = structlog.get_logger(__name__)

# Attempt to import ML libraries — graceful fallback if not installed
try:
    import joblib
    import xgboost as xgb
    _ML_AVAILABLE = True
except ImportError:
    _ML_AVAILABLE = False
    log.warning("ml_libraries_not_available", fallback="rule-based prediction")

MODELS_DIR = Path(__file__).parent.parent.parent.parent.parent / "models"
MODEL_VERSION = "v1"

FEATURE_NAMES = [
    "rainfall_intensity_mm_hr",
    "rainfall_duration_hr",
    "accumulated_rainfall_mm",
    "drainage_utilization_pct",
    "drainage_surcharging_nodes",
    "catchment_imperviousness",
    "catchment_cn",
    "catchment_area_ha",
    "terrain_elevation_m",
    "terrain_slope_pct",
    "terrain_susceptibility",
    "antecedent_moisture_mm",
    "time_since_last_rain_hr",
    "horizon_minutes",
]


class MLPrediction(NamedTuple):
    flood_probability: float     # 0.0–1.0
    flood_depth_cm: float        # ≥ 0.0
    confidence: float            # 0.0–1.0
    model_used: str              # "xgboost_v1" or "rule_based_fallback"


class FloodMLPredictor:
    """
    Flood prediction inference using trained XGBoost models.

    Falls back to rule-based prediction if models are not loaded.
    Every prediction includes model_used field for transparency.
    """

    def __init__(self) -> None:
        self._classifier: Optional[object] = None
        self._regressor: Optional[object] = None
        self._scaler: Optional[object] = None
        self._loaded: bool = False
        self._metadata: Dict = {}
        self._load_models()

    def _load_models(self) -> None:
        """Load trained models from disk. Silently falls back if unavailable."""
        if not _ML_AVAILABLE:
            log.warning("ml_predictor_fallback", reason="xgboost/joblib not installed")
            return

        clf_path  = MODELS_DIR / f"xgboost_classifier_{MODEL_VERSION}.json"
        reg_path  = MODELS_DIR / f"xgboost_regressor_{MODEL_VERSION}.json"
        sca_path  = MODELS_DIR / f"scaler_{MODEL_VERSION}.pkl"
        meta_path = MODELS_DIR / f"training_metadata_{MODEL_VERSION}.json"

        if not clf_path.exists():
            log.warning(
                "ml_models_not_found",
                path=str(clf_path),
                hint="Run: python scripts/train_models.py",
            )
            return

        try:
            clf = xgb.XGBClassifier()
            clf.load_model(str(clf_path))
            self._classifier = clf

            if reg_path.exists():
                reg = xgb.XGBRegressor()
                reg.load_model(str(reg_path))
                self._regressor = reg

            if sca_path.exists():
                self._scaler = joblib.load(str(sca_path))

            if meta_path.exists():
                with open(meta_path) as f:
                    self._metadata = json.load(f)

            self._loaded = True
            log.info(
                "ml_models_loaded",
                version=MODEL_VERSION,
                classifier=str(clf_path.name),
                regressor=str(reg_path.name) if reg_path.exists() else "none",
            )
        except Exception as e:
            log.error("ml_model_load_failed", error=str(e))
            self._loaded = False

    def predict(
        self,
        rainfall_intensity_mm_hr: float,
        rainfall_duration_hr: float,
        accumulated_rainfall_mm: float,
        drainage_utilization_pct: float,
        drainage_surcharging_nodes: int,
        catchment_imperviousness: float,
        catchment_cn: int,
        catchment_area_ha: float,
        terrain_elevation_m: float,
        terrain_slope_pct: float,
        terrain_susceptibility: float,
        antecedent_moisture_mm: float,
        time_since_last_rain_hr: float,
        horizon_minutes: int,
    ) -> MLPrediction:
        """
        Run ML inference for a single location/horizon combination.

        Returns MLPrediction with flood_probability, flood_depth_cm,
        confidence, and model_used tag.
        """
        features = np.array([[
            rainfall_intensity_mm_hr,
            rainfall_duration_hr,
            accumulated_rainfall_mm,
            drainage_utilization_pct,
            float(drainage_surcharging_nodes),
            catchment_imperviousness,
            float(catchment_cn),
            catchment_area_ha,
            terrain_elevation_m,
            terrain_slope_pct,
            terrain_susceptibility,
            antecedent_moisture_mm,
            time_since_last_rain_hr,
            float(horizon_minutes),
        ]], dtype=np.float32)

        if self._loaded and self._classifier is not None:
            try:
                # Scale features
                if self._scaler is not None:
                    features_s = self._scaler.transform(features)
                else:
                    features_s = features

                # Classification: flood probability
                prob = float(self._classifier.predict_proba(features_s)[0, 1])

                # Regression: depth (only if flooding predicted)
                if self._regressor is not None and prob > 0.3:
                    depth = float(max(0.0, self._regressor.predict(features_s)[0]))
                else:
                    depth = max(0.0, prob * rainfall_intensity_mm_hr * 0.15)

                # Confidence: higher near boundaries = less certain
                boundary_uncertainty = abs(prob - 0.5) * 0.2
                base_confidence = 0.75 + boundary_uncertainty
                horizon_penalty = 0.003 * horizon_minutes
                confidence = max(0.40, min(0.90, base_confidence - horizon_penalty))

                return MLPrediction(
                    flood_probability=round(prob, 4),
                    flood_depth_cm=round(depth, 2),
                    confidence=round(confidence, 3),
                    model_used=f"xgboost_{MODEL_VERSION}",
                )
            except Exception as e:
                log.error("ml_inference_failed", error=str(e), fallback="rule_based")

        # Rule-based fallback
        return self._rule_based_fallback(
            rainfall_intensity_mm_hr,
            drainage_utilization_pct,
            catchment_imperviousness,
            terrain_susceptibility,
            horizon_minutes,
        )

    def _rule_based_fallback(
        self,
        intensity: float,
        util: float,
        imperv: float,
        susceptibility: float,
        horizon_min: int,
    ) -> MLPrediction:
        """Rule-based fallback when ML models are unavailable."""
        import math
        # Simple sigmoid on normalized stress index
        stress = (intensity / 100.0) * 0.4 + (util / 150.0) * 0.3 + imperv * 0.2 + susceptibility * 0.1
        prob = 1.0 / (1.0 + math.exp(-10 * (stress - 0.5)))
        depth = max(0.0, (intensity - 20.0) * 0.1 * imperv) if intensity > 20 else 0.0
        confidence = max(0.40, 0.70 - 0.003 * horizon_min)
        return MLPrediction(
            flood_probability=round(prob, 4),
            flood_depth_cm=round(depth, 2),
            confidence=round(confidence, 3),
            model_used="rule_based_fallback",
        )

    def explain_prediction(
        self,
        rainfall_intensity_mm_hr: float,
        accumulated_rainfall_mm: float,
        drainage_utilization_pct: float,
        drainage_surcharging_nodes: int,
        catchment_imperviousness: float,
        catchment_cn: int,
        terrain_elevation_m: float,
        terrain_susceptibility: float,
        antecedent_moisture_mm: float,
        horizon_minutes: int = 60,
    ) -> Dict:
        """
        Return per-feature contributions for a prediction (XGBoost gain-weighted).

        Methodology:
          contribution_i = feature_importance_i × normalized_feature_value_i
          Normalized relative to all 14 features for this sample.

        This is an approximation of SHAP marginal contributions.
        True SHAP requires the `shap` library; this uses XGBoost's built-in
        feature_importances_ (gain) weighted by feature magnitude.

        Returns dict with:
          - contributions: list of {feature, value, raw_value, direction, rank}
          - flood_probability: float
          - model_used: str
        """
        rainfall_duration_hr = max(0.5, accumulated_rainfall_mm / max(rainfall_intensity_mm_hr, 0.1))
        time_since_last_rain_hr = 0.0

        pred = self.predict(
            rainfall_intensity_mm_hr=rainfall_intensity_mm_hr,
            rainfall_duration_hr=rainfall_duration_hr,
            accumulated_rainfall_mm=accumulated_rainfall_mm,
            drainage_utilization_pct=drainage_utilization_pct,
            drainage_surcharging_nodes=drainage_surcharging_nodes,
            catchment_imperviousness=catchment_imperviousness,
            catchment_cn=catchment_cn,
            catchment_area_ha=350.0,
            terrain_elevation_m=terrain_elevation_m,
            terrain_slope_pct=0.5,
            terrain_susceptibility=terrain_susceptibility,
            antecedent_moisture_mm=antecedent_moisture_mm,
            time_since_last_rain_hr=time_since_last_rain_hr,
            horizon_minutes=horizon_minutes,
        )

        # Raw feature values for all 14 features
        raw_values = [
            rainfall_intensity_mm_hr,
            rainfall_duration_hr,
            accumulated_rainfall_mm,
            drainage_utilization_pct,
            float(drainage_surcharging_nodes),
            catchment_imperviousness,
            float(catchment_cn),
            350.0,           # catchment_area_ha
            terrain_elevation_m,
            0.5,             # terrain_slope_pct
            terrain_susceptibility,
            antecedent_moisture_mm,
            time_since_last_rain_hr,
            float(horizon_minutes),
        ]

        # Normalize features 0–1 for contribution calculation
        feature_ranges = [
            150.0,   # rainfall_intensity_mm_hr (max 150)
            12.0,    # rainfall_duration_hr
            300.0,   # accumulated_rainfall_mm
            200.0,   # drainage_utilization_pct
            30.0,    # drainage_surcharging_nodes
            1.0,     # catchment_imperviousness
            100.0,   # catchment_cn
            1000.0,  # catchment_area_ha
            20.0,    # terrain_elevation_m
            5.0,     # terrain_slope_pct
            1.0,     # terrain_susceptibility
            100.0,   # antecedent_moisture_mm
            72.0,    # time_since_last_rain_hr
            180.0,   # horizon_minutes
        ]
        normalized = [min(1.0, abs(v) / r) for v, r in zip(raw_values, feature_ranges)]

        # Get XGBoost feature importances if loaded
        if self._loaded and self._classifier is not None:
            try:
                importances = self._classifier.feature_importances_
            except Exception:
                importances = np.ones(14) / 14.0
        else:
            # Fallback importances from ML model card
            importances = np.array([
                0.3449, 0.0760, 0.3324, 0.0197, 0.0514,
                0.0481, 0.0220, 0.0050, 0.0182, 0.0050,
                0.0287, 0.0388, 0.0050, 0.0048,
            ])

        # Contribution = importance × normalized_magnitude
        contributions_raw = importances * np.array(normalized)
        total = max(contributions_raw.sum(), 1e-9)

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

        contributions = []
        for i, fname in enumerate(FEATURE_NAMES):
            pct = float(contributions_raw[i] / total * 100)
            contributions.append({
                "feature": fname,
                "label": human_names.get(fname, fname),
                "raw_value": round(raw_values[i], 3),
                "importance": round(float(importances[i]), 4),
                "contribution_pct": round(pct, 2),
                "direction": "increases_risk" if raw_values[i] > 0 else "neutral",
            })

        contributions.sort(key=lambda x: x["contribution_pct"], reverse=True)
        for i, c in enumerate(contributions):
            c["rank"] = i + 1

        return {
            "flood_probability": pred.flood_probability,
            "flood_depth_cm": pred.flood_depth_cm,
            "confidence": pred.confidence,
            "model_used": pred.model_used,
            "contributions": contributions,
            "methodology": "XGBoost gain-weighted feature contribution (approximation of SHAP marginal values)",
            "data_source": "SYNTHETIC_PROTOTYPE",
            "disclaimer": "Feature contributions are approximate. Install shap library for exact Shapley values.",
        }

    def predict_batch(self, feature_dicts: List[Dict]) -> List[MLPrediction]:
        """Batch prediction for multiple locations/horizons."""
        return [self.predict(**fd) for fd in feature_dicts]

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_version(self) -> str:
        return MODEL_VERSION if self._loaded else "rule_based_fallback"

    @property
    def metadata(self) -> Dict:
        return self._metadata


# Module-level singleton — loaded once at startup
ml_predictor = FloodMLPredictor()
