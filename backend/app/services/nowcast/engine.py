"""
FLOOD-X Nowcast Engine — 0 to 3 Hour Predictions
=================================================
Generates per-location flood predictions at 15-minute intervals.

METHODOLOGY:
  1. Get current rainfall from provider
  2. Run SCS-CN hydrology for each catchment
  3. Estimate drainage utilization per node
  4. Run ML model (or fallback rule-based if model not loaded)
  5. Compute risk level and depth
  6. Propagate forward using simple decay/growth model

ASSUMPTIONS:
  - Rainfall forecast uses exponential decay model
  - Depth estimate uses Manning's shallow flow approximation
  - No full hydrodynamic routing (prototype limitation)

DATA SOURCE: SYNTHETIC_PROTOTYPE inputs → MODELLED outputs
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import structlog

from app.providers import synthetic_rainfall, synthetic_drainage
from app.schemas import (
    DataProvenance,
    DataSourceType,
    FloodClock,
    FloodClockEntry,
    FloodClockStatus,
    LocationNowcast,
    NowcastHorizon,
    RiskLevel,
)
from app.services.hydrology.engine import hydrology_engine, SYNTHETIC_CATCHMENTS
from app.services.risk.engine import risk_engine, RiskInput

log = structlog.get_logger(__name__)

# Prediction horizons in minutes
HORIZONS_MIN = [0, 15, 30, 45, 60, 90, 120, 150, 180]

# Depth thresholds for risk level transitions (cm)
DEPTH_THRESHOLDS = {
    FloodClockStatus.WATCH: 5.0,
    FloodClockStatus.WARNING: 20.0,
    FloodClockStatus.CRITICAL: 45.0,
}


def _depth_from_runoff(runoff_mm: float, surface_acc_mm: float) -> float:
    """
    Estimate surface flood depth from runoff excess.

    SIMPLIFIED MODEL: depth ≈ surface_accumulation × scaling factor
    Not a full hydrodynamic solver. Documented limitation.
    """
    # Combined surface accumulation and runoff contribution
    total_mm = surface_acc_mm + runoff_mm * 0.15
    # Urban flood depths scale roughly with mm ponding
    depth_cm = total_mm * 0.8  # empirical scaling for prototype
    return max(0.0, depth_cm)


def _confidence_from_horizon(horizon_min: int, intensity: float) -> float:
    """Confidence decreases with forecast horizon and high rainfall variability."""
    base = 0.90
    decay = 0.003 * horizon_min  # 0.9% per 15 min
    variability_penalty = 0.10 if intensity > 60 else 0.0
    return max(0.40, base - decay - variability_penalty)


class NowcastEngine:
    """Generates 0–3 hour flood nowcasts for all Chennai pilot locations."""

    def __init__(self) -> None:
        self._current_intensity: float = 0.0
        self._accumulated_mm: float = 0.0
        self._scenario: str = "normal_rainfall"

    def update_state(
        self,
        intensity_mm_hr: float,
        accumulated_mm: float,
        scenario: str = "normal_rainfall",
    ) -> None:
        self._current_intensity = intensity_mm_hr
        self._accumulated_mm = accumulated_mm
        self._scenario = scenario

    async def generate_nowcasts(self) -> List[LocationNowcast]:
        """Generate nowcasts for all pilot catchment locations."""
        now = datetime.now(timezone.utc)
        intensity = self._current_intensity
        accumulated = self._accumulated_mm

        # Get drainage status for current state
        drainage_status = await synthetic_drainage.get_network_status(intensity)
        node_utilization: Dict[str, float] = {
            n.node_id: n.utilization_pct for n in drainage_status.nodes
        }

        nowcasts = []

        for cat in SYNTHETIC_CATCHMENTS:
            horizons = []
            prev_depth = 0.0

            for h_min in HORIZONS_MIN:
                # Forecast intensity: exponential decay
                decay = math.exp(-0.008 * h_min)
                future_intensity = intensity * decay

                # Runoff at this horizon
                runoff_results = hydrology_engine.calculate_runoff(
                    future_intensity, duration_min=15.0, accumulated_mm=accumulated + future_intensity * h_min / 60.0
                )

                cat_runoff = next(
                    (r for r in runoff_results if r.catchment_id == cat["id"]),
                    None,
                )
                if not cat_runoff:
                    continue

                # Drainage utilization at this node
                util = node_utilization.get(cat["drainage_node"], 50.0)
                # Future utilization also decays
                future_util = util * decay * (1.0 + 0.2 * (h_min / 180.0))  # slight lag

                # Depth estimate
                depth_cm = _depth_from_runoff(
                    cat_runoff.rainfall_excess_mm,
                    cat_runoff.surface_accumulation_mm,
                )
                # Depth has inertia — only decreases slowly
                if h_min > 0:
                    depth_cm = max(depth_cm, prev_depth * 0.85)
                prev_depth = depth_cm

                # ML risk score (rule-based fallback for now — ML wires in M8)
                risk_inp = RiskInput(
                    location_id=cat["id"],
                    flood_probability=min(1.0, depth_cm / 60.0),
                    drainage_utilization_pct=future_util,
                    predicted_depth_cm=depth_cm,
                    rainfall_intensity_mm_hr=future_intensity,
                    terrain_susceptibility=1.0 - (cat.get("area_ha", 1000) / 2500.0),
                )
                risk_out = risk_engine.score(risk_inp)
                prob = risk_inp.flood_probability
                confidence = _confidence_from_horizon(h_min, intensity)

                horizons.append(NowcastHorizon(
                    horizon_minutes=h_min,
                    forecast_time=now + timedelta(minutes=h_min),
                    flood_probability=round(prob, 4),
                    estimated_depth_cm=round(depth_cm, 2),
                    risk_level=risk_out.risk_level,
                    confidence=round(confidence, 3),
                ))

            if not horizons:
                continue

            current = horizons[0]
            provenance = DataProvenance(
                source=DataSourceType.MODELLED,
                provider="NowcastEngine v1",
                model_method="SCS-CN + Rational Method + Risk Scoring",
                model_version="1.0.0",
                timestamp=now,
                confidence=horizons[0].confidence,
                assumptions=[
                    "Rainfall forecast: exponential decay model",
                    "Depth: simplified surface ponding estimate",
                    "Not a full hydrodynamic solver",
                    "Input data: SYNTHETIC_PROTOTYPE",
                ],
            )

            nowcasts.append(LocationNowcast(
                location_id=cat["id"],
                location_name=cat["name"],
                latitude=cat["centroid_lat"],
                longitude=cat["centroid_lon"],
                current_risk=current.risk_level,
                current_depth_cm=current.estimated_depth_cm,
                horizons=horizons,
                provenance=provenance,
            ))

        return nowcasts

    async def get_flood_clock(self, location_id: str) -> Optional[FloodClock]:
        """Generate Flood Clock for a specific location."""
        nowcasts = await self.generate_nowcasts()
        nc = next((n for n in nowcasts if n.location_id == location_id), None)
        if not nc:
            return None

        now = datetime.now(timezone.utc)
        timeline = []
        time_to_watch = None
        time_to_warning = None
        time_to_critical = None

        for h in nc.horizons:
            if h.estimated_depth_cm < DEPTH_THRESHOLDS[FloodClockStatus.WATCH]:
                status = FloodClockStatus.SAFE
            elif h.estimated_depth_cm < DEPTH_THRESHOLDS[FloodClockStatus.WARNING]:
                status = FloodClockStatus.WATCH
                if time_to_watch is None:
                    time_to_watch = h.horizon_minutes
            elif h.estimated_depth_cm < DEPTH_THRESHOLDS[FloodClockStatus.CRITICAL]:
                status = FloodClockStatus.WARNING
                if time_to_warning is None:
                    time_to_warning = h.horizon_minutes
            else:
                status = FloodClockStatus.CRITICAL
                if time_to_critical is None:
                    time_to_critical = h.horizon_minutes

            timeline.append(FloodClockEntry(
                status=status,
                minutes_from_now=h.horizon_minutes,
                estimated_depth_cm=h.estimated_depth_cm,
                flood_probability=h.flood_probability,
            ))

        current_status = timeline[0].status if timeline else FloodClockStatus.SAFE
        peak_depth = max((t.estimated_depth_cm for t in timeline), default=0.0)
        avg_confidence = sum(h.confidence for h in nc.horizons) / max(len(nc.horizons), 1)

        return FloodClock(
            location_id=nc.location_id,
            location_name=nc.location_name,
            latitude=nc.latitude,
            longitude=nc.longitude,
            current_status=current_status,
            time_to_watch_min=time_to_watch,
            time_to_warning_min=time_to_warning,
            time_to_critical_min=time_to_critical,
            estimated_peak_depth_cm=round(peak_depth, 2),
            confidence=round(avg_confidence, 3),
            timeline=timeline,
            last_updated=now,
            provenance=nc.provenance,
        )


# Singleton
nowcast_engine = NowcastEngine()
