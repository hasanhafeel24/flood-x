"""
Unit tests for FLOOD-X ML Predictor
=====================================
Tests inference, fallback behaviour, and output validity.
"""
import pytest
from app.services.ml.predictor import FloodMLPredictor, MLPrediction


def _make_predictor() -> FloodMLPredictor:
    return FloodMLPredictor()


BASE_FEATURES = dict(
    rainfall_intensity_mm_hr=50.0,
    rainfall_duration_hr=2.0,
    accumulated_rainfall_mm=30.0,
    drainage_utilization_pct=120.0,
    drainage_surcharging_nodes=2,
    catchment_imperviousness=0.80,
    catchment_cn=88,
    catchment_area_ha=1200.0,
    terrain_elevation_m=2.5,
    terrain_slope_pct=1.5,
    terrain_susceptibility=0.75,
    antecedent_moisture_mm=25.0,
    time_since_last_rain_hr=1.0,
    horizon_minutes=30,
)


class TestMLPredictorOutputValidity:
    """Test that all ML outputs are valid regardless of model state."""

    def test_flood_probability_in_range(self):
        predictor = _make_predictor()
        pred = predictor.predict(**BASE_FEATURES)
        assert 0.0 <= pred.flood_probability <= 1.0

    def test_depth_non_negative(self):
        predictor = _make_predictor()
        pred = predictor.predict(**BASE_FEATURES)
        assert pred.flood_depth_cm >= 0.0

    def test_confidence_in_range(self):
        predictor = _make_predictor()
        pred = predictor.predict(**BASE_FEATURES)
        assert 0.0 <= pred.confidence <= 1.0

    def test_model_used_is_string(self):
        predictor = _make_predictor()
        pred = predictor.predict(**BASE_FEATURES)
        assert isinstance(pred.model_used, str)
        assert len(pred.model_used) > 0

    def test_returns_ml_prediction_type(self):
        predictor = _make_predictor()
        pred = predictor.predict(**BASE_FEATURES)
        assert isinstance(pred, MLPrediction)

    def test_zero_rainfall_low_probability(self):
        """Zero rainfall should give low flood probability."""
        predictor = _make_predictor()
        features = {**BASE_FEATURES,
                    "rainfall_intensity_mm_hr": 0.0,
                    "accumulated_rainfall_mm": 0.0,
                    "drainage_utilization_pct": 20.0,
                    "drainage_surcharging_nodes": 0}
        pred = predictor.predict(**features)
        # Should not be CRITICAL under zero rain
        assert pred.flood_probability < 0.9

    def test_extreme_rain_high_probability(self):
        """Extreme rainfall + high drainage utilization → high flood probability."""
        predictor = _make_predictor()
        features = {**BASE_FEATURES,
                    "rainfall_intensity_mm_hr": 150.0,
                    "accumulated_rainfall_mm": 100.0,
                    "drainage_utilization_pct": 200.0,
                    "drainage_surcharging_nodes": 10}
        pred = predictor.predict(**features)
        assert pred.flood_probability > 0.5

    def test_horizon_0_higher_confidence_than_180(self):
        """Nowcast at T+0 should have >= confidence than T+180."""
        predictor = _make_predictor()
        pred_now  = predictor.predict(**{**BASE_FEATURES, "horizon_minutes": 0})
        pred_far  = predictor.predict(**{**BASE_FEATURES, "horizon_minutes": 180})
        # Confidence should generally decrease with horizon
        # Allow small tolerance for model boundary effects
        assert pred_now.confidence >= pred_far.confidence - 0.05


class TestMLPredictorFallback:
    """Test graceful fallback when models are not available."""

    def test_fallback_returns_valid_prediction(self):
        """Rule-based fallback must still return valid MLPrediction."""
        predictor = _make_predictor()
        # Force fallback by calling private method directly
        pred = predictor._rule_based_fallback(
            intensity=60.0,
            util=130.0,
            imperv=0.80,
            susceptibility=0.75,
            horizon_min=30,
        )
        assert isinstance(pred, MLPrediction)
        assert 0.0 <= pred.flood_probability <= 1.0
        assert pred.flood_depth_cm >= 0.0
        assert pred.model_used == "rule_based_fallback"

    def test_is_loaded_reflects_model_state(self):
        """is_loaded must be bool."""
        predictor = _make_predictor()
        assert isinstance(predictor.is_loaded, bool)

    def test_model_version_is_string(self):
        """model_version returns a non-empty string."""
        predictor = _make_predictor()
        assert isinstance(predictor.model_version, str)
        assert len(predictor.model_version) > 0
