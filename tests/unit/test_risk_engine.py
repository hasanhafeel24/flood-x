"""
Unit tests for FLOOD-X Risk Engine
=====================================
Tests weighted scoring, risk levels, and component validation.
"""
import pytest
from app.services.risk.engine import RiskEngine, RiskInput, RiskOutput, risk_engine
from app.schemas import RiskLevel


class TestRiskEngineScoring:
    """Test risk score computation."""

    def test_all_zero_input_gives_low_risk(self):
        """No rainfall, no drainage load → LOW risk."""
        engine = RiskEngine()
        inp = RiskInput(
            location_id="test",
            flood_probability=0.0,
            drainage_utilization_pct=0.0,
            predicted_depth_cm=0.0,
            rainfall_intensity_mm_hr=0.0,
            terrain_susceptibility=0.0,
        )
        result = engine.score(inp)
        assert result.risk_level == RiskLevel.LOW
        assert result.risk_score < 0.30

    def test_all_max_input_gives_critical_risk(self):
        """Maximum stress on all inputs → CRITICAL."""
        engine = RiskEngine()
        inp = RiskInput(
            location_id="test",
            flood_probability=1.0,
            drainage_utilization_pct=200.0,
            predicted_depth_cm=100.0,
            rainfall_intensity_mm_hr=200.0,
            terrain_susceptibility=1.0,
        )
        result = engine.score(inp)
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.risk_score >= 0.80

    def test_weights_sum_to_one(self):
        """Component weights must sum to exactly 1.0."""
        engine = RiskEngine()
        total = sum(engine.WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, not 1.0"

    def test_risk_score_clamped_between_0_and_1(self):
        """Risk score is always between 0 and 1."""
        engine = RiskEngine()
        for prob in [0.0, 0.5, 1.0]:
            for util in [0.0, 100.0, 250.0]:
                inp = RiskInput(
                    location_id="test",
                    flood_probability=prob,
                    drainage_utilization_pct=util,
                    predicted_depth_cm=50.0,
                    rainfall_intensity_mm_hr=80.0,
                    terrain_susceptibility=0.5,
                )
                result = engine.score(inp)
                assert 0.0 <= result.risk_score <= 1.0

    def test_risk_monotonically_increases_with_probability(self):
        """Higher flood probability → equal or higher risk score."""
        engine = RiskEngine()
        scores = []
        for prob in [0.0, 0.2, 0.5, 0.8, 1.0]:
            inp = RiskInput(
                location_id="test",
                flood_probability=prob,
                drainage_utilization_pct=80.0,
                predicted_depth_cm=20.0,
                rainfall_intensity_mm_hr=50.0,
                terrain_susceptibility=0.5,
            )
            scores.append(engine.score(inp).risk_score)

        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i+1], \
                f"Score not monotone at prob step {i}: {scores}"

    def test_thresholds_match_levels(self):
        """Risk levels transition at documented thresholds."""
        engine = RiskEngine()

        # Just below MODERATE threshold
        inp_low = RiskInput("x", flood_probability=0.0, drainage_utilization_pct=0.0,
                            predicted_depth_cm=0.0, rainfall_intensity_mm_hr=0.0,
                            terrain_susceptibility=0.0)
        assert engine.score(inp_low).risk_level == RiskLevel.LOW

    def test_dominant_factor_is_valid_key(self):
        """dominant_factor must be one of the weight keys."""
        engine = RiskEngine()
        inp = RiskInput("x", 0.7, 120.0, 30.0, 70.0, 0.6)
        result = engine.score(inp)
        assert result.dominant_factor in engine.WEIGHTS

    def test_score_many_returns_correct_count(self):
        """score_many returns one result per input."""
        engine = RiskEngine()
        inputs = [
            RiskInput(f"loc_{i}", 0.5, 80.0, 20.0, 50.0, 0.5)
            for i in range(10)
        ]
        results = engine.score_many(inputs)
        assert len(results) == 10

    def test_component_scores_in_range(self):
        """All component scores are between 0 and 1."""
        engine = RiskEngine()
        inp = RiskInput("x", 0.8, 150.0, 45.0, 90.0, 0.7)
        result = engine.score(inp)
        for k, v in result.component_scores.items():
            assert 0.0 <= v <= 1.0, f"Component {k} = {v} out of range"

    def test_singleton_is_same_object(self):
        """risk_engine singleton is always the same object."""
        from app.services.risk.engine import risk_engine as re1
        from app.services.risk.engine import risk_engine as re2
        assert re1 is re2
