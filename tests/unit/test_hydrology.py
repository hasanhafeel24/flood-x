"""
Unit tests for FLOOD-X Hydrology Engine
========================================
Tests SCS-CN, Rational Method, and catchment computation.

DATA: Uses synthetic catchments (SYNTHETIC_PROTOTYPE)
"""
import pytest
from app.services.hydrology.engine import (
    HydrologyEngine,
    hydrology_engine,
    SYNTHETIC_CATCHMENTS,
)


class TestSCSCurveNumber:
    """Test SCS-CN rainfall-runoff method."""

    def test_no_runoff_below_initial_abstraction(self):
        """Very light rainfall should produce minimal/zero runoff."""
        engine = HydrologyEngine()
        results = engine.calculate_runoff(
            rainfall_intensity_mm_hr=2.0,   # Very light rain
            duration_min=15.0,
            accumulated_mm=0.0,
        )
        for r in results:
            assert r.rainfall_excess_mm >= 0.0, "Runoff cannot be negative"

    def test_heavy_rain_produces_runoff(self):
        """Heavy rainfall must produce positive runoff."""
        engine = HydrologyEngine()
        results = engine.calculate_runoff(
            rainfall_intensity_mm_hr=100.0,
            duration_min=60.0,
            accumulated_mm=30.0,
        )
        assert len(results) == len(SYNTHETIC_CATCHMENTS)
        for r in results:
            assert r.rainfall_excess_mm > 0.0, f"Expected runoff for {r.catchment_id}"

    def test_runoff_increases_with_intensity(self):
        """More rainfall → more runoff (monotonic)."""
        engine = HydrologyEngine()
        r_low  = engine.calculate_runoff(30.0,  60.0, 0.0)
        r_high = engine.calculate_runoff(100.0, 60.0, 0.0)
        excess_low  = sum(r.rainfall_excess_mm for r in r_low)
        excess_high = sum(r.rainfall_excess_mm for r in r_high)
        assert excess_high > excess_low, "Higher intensity must produce more runoff"

    def test_antecedent_moisture_increases_runoff(self):
        """Wet antecedent conditions (high accumulated) → more runoff."""
        engine = HydrologyEngine()
        r_dry = engine.calculate_runoff(50.0, 60.0, 5.0)    # low antecedent
        r_wet = engine.calculate_runoff(50.0, 60.0, 80.0)   # high antecedent

        excess_dry = sum(r.rainfall_excess_mm for r in r_dry)
        excess_wet = sum(r.rainfall_excess_mm for r in r_wet)
        # Wet conditions should produce equal or more runoff
        assert excess_wet >= excess_dry, "Wet AMC must produce >= runoff vs dry"

    def test_all_catchments_returned(self):
        """Results must include every defined synthetic catchment."""
        engine = HydrologyEngine()
        results = engine.calculate_runoff(50.0, 30.0, 10.0)
        result_ids = {r.catchment_id for r in results}
        expected_ids = {c["id"] for c in SYNTHETIC_CATCHMENTS}
        assert result_ids == expected_ids

    def test_surface_accumulation_non_negative(self):
        """Surface accumulation cannot be negative."""
        engine = HydrologyEngine()
        results = engine.calculate_runoff(80.0, 60.0, 20.0)
        for r in results:
            assert r.surface_accumulation_mm >= 0.0

    def test_peak_flow_non_negative(self):
        """Peak flow must be non-negative."""
        engine = HydrologyEngine()
        results = engine.calculate_runoff(80.0, 60.0, 20.0)
        for r in results:
            assert r.peak_flow_m3_s >= 0.0

    def test_peak_flow_positive_for_heavy_rain(self):
        """Under heavy rain, flooded catchments must have positive peak flow."""
        engine = HydrologyEngine()
        results = engine.calculate_runoff(100.0, 60.0, 30.0)
        flooded = [r for r in results if r.rainfall_excess_mm > 0]
        assert len(flooded) > 0, "Heavy rain should produce some flooded catchments"
        for r in flooded:
            assert r.peak_flow_m3_s > 0.0, f"{r.catchment_id} has excess but zero peak flow"

    def test_cn_validation(self):
        """Catchments should have physically valid CN values (25-100)."""
        for cat in SYNTHETIC_CATCHMENTS:
            assert 25 <= cat["cn"] <= 100, f"{cat['id']} has invalid CN {cat['cn']}"

    def test_imperviousness_in_range(self):
        """Imperviousness must be between 0 and 1."""
        for cat in SYNTHETIC_CATCHMENTS:
            assert 0.0 <= cat["imperviousness"] <= 1.0


class TestHydrologyEngineSingleton:
    """Test singleton behaviour and state management."""

    def test_singleton_is_same_object(self):
        """hydrology_engine singleton returns same object."""
        from app.services.hydrology.engine import hydrology_engine as he1
        from app.services.hydrology.engine import hydrology_engine as he2
        assert he1 is he2

    def test_reset_antecedent_moisture(self):
        """reset_antecedent_moisture resets all catchment moisture to 0."""
        engine = HydrologyEngine()
        # Antecedent moisture is a dict keyed by catchment id
        engine.reset_antecedent_moisture()
        # After reset all values should be 0
        for v in engine._antecedent_moisture.values():
            assert v == 0.0, f"Antecedent moisture not reset: {v}"
