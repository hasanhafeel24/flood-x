"""
FLOOD-X Synthetic Data Provider — Chennai Pilot Context
========================================================
DATA SOURCE: SYNTHETIC_PROTOTYPE
All data in this module is SYNTHETIC — generated algorithmically for
demonstration purposes. It is NOT real IMD data, NOT real sensor data,
and NOT real municipal drainage data.

The provider abstraction ensures real data can replace this
without changing the service layer.
"""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.schemas import (
    DataProvenance,
    DataSourceType,
    DrainageNetworkStatus,
    DrainageNodeStatus,
    DrainageNodeType,
    RainfallObservation,
    RiskLevel,
)

# ── Provider Interfaces ────────────────────────────────────────────────────────


class RainfallProvider(ABC):
    """Abstract interface for rainfall data providers.

    Implement this interface to add new data sources (e.g., IMD, AWS sensors).
    The service layer depends only on this interface.
    """

    @abstractmethod
    async def get_current(self) -> RainfallObservation:
        """Return the most recent rainfall observation."""
        ...

    @abstractmethod
    async def get_forecast(self, hours: int = 3) -> List[RainfallObservation]:
        """Return rainfall forecast at 15-minute intervals for `hours` ahead."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def data_source_type(self) -> DataSourceType:
        ...


class DrainageProvider(ABC):
    """Abstract interface for drainage network data providers."""

    @abstractmethod
    async def get_network_status(
        self, rainfall_mm_hr: float, scenario_modifier: float = 1.0
    ) -> DrainageNetworkStatus:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...


# ── Scenario Definitions ──────────────────────────────────────────────────────

SCENARIOS: Dict[str, Dict] = {
    "normal_rainfall": {
        "label": "Normal Rainfall",
        "intensity_mm_hr": 8.0,
        "duration_hr": 2.0,
        "description": "Light to moderate rainfall — typical Chennai monsoon",
    },
    "heavy_rainfall": {
        "label": "Heavy Rainfall",
        "intensity_mm_hr": 35.0,
        "duration_hr": 3.0,
        "description": "Heavy rainfall — drainage load approaching capacity",
    },
    "extreme_rainfall": {
        "label": "Extreme Rainfall",
        "intensity_mm_hr": 85.0,
        "duration_hr": 4.0,
        "description": "Extreme rainfall — Chennai 2015-type event",
    },
    "short_intense_storm": {
        "label": "Short Intense Storm",
        "intensity_mm_hr": 120.0,
        "duration_hr": 0.75,
        "description": "Cloudburst event — rapid drainage overload",
    },
    "prolonged_rainfall": {
        "label": "Prolonged Rainfall",
        "intensity_mm_hr": 20.0,
        "duration_hr": 12.0,
        "description": "Sustained moderate rainfall — saturation risk",
    },
    "drainage_blockage": {
        "label": "Drainage Blockage",
        "intensity_mm_hr": 30.0,
        "duration_hr": 2.0,
        "description": "Heavy rainfall with 40% drainage capacity reduction",
        "drainage_modifier": 0.6,
    },
    "pump_failure": {
        "label": "Pump Failure",
        "intensity_mm_hr": 40.0,
        "duration_hr": 2.5,
        "description": "Heavy rainfall with pump stations offline",
        "drainage_modifier": 0.45,
    },
    "combined_extreme": {
        "label": "Combined Extreme",
        "intensity_mm_hr": 95.0,
        "duration_hr": 5.0,
        "description": "Extreme rainfall + drainage stress — worst-case scenario",
        "drainage_modifier": 0.5,
    },
}


# ── Chennai Synthetic Drainage Network ────────────────────────────────────────
# 30 representative nodes covering flood-prone zones
# SYNTHETIC_PROTOTYPE — not real CMWSSB data

CHENNAI_SYNTHETIC_NODES = [
    # Zone: Adyar river basin (historically flood-prone)
    {"id": "N001", "name": "Adyar River Outfall", "type": "outfall",
     "lat": 13.0100, "lon": 80.2650, "elev": 1.2, "capacity": 85.0},
    {"id": "N002", "name": "Adyar Estuary Pump", "type": "pump",
     "lat": 13.0120, "lon": 80.2600, "elev": 1.8, "capacity": 45.0},
    {"id": "N003", "name": "Kotturpuram Junction", "type": "junction",
     "lat": 13.0178, "lon": 80.2534, "elev": 5.2, "capacity": 12.0},
    {"id": "N004", "name": "Saidapet Manhole", "type": "manhole",
     "lat": 13.0219, "lon": 80.2214, "elev": 7.4, "capacity": 8.5},
    {"id": "N005", "name": "Guindy Storage Basin", "type": "storage",
     "lat": 13.0069, "lon": 80.2206, "elev": 6.1, "capacity": 120.0},
    # Zone: Cooum river basin
    {"id": "N006", "name": "Cooum River Outfall", "type": "outfall",
     "lat": 13.0827, "lon": 80.2935, "elev": 0.8, "capacity": 70.0},
    {"id": "N007", "name": "Park Town Junction", "type": "junction",
     "lat": 13.0827, "lon": 80.2707, "elev": 4.1, "capacity": 10.0},
    {"id": "N008", "name": "Anna Nagar Manhole", "type": "manhole",
     "lat": 13.0850, "lon": 80.2101, "elev": 12.3, "capacity": 7.0},
    {"id": "N009", "name": "Thirumangalam Inlet", "type": "inlet",
     "lat": 13.0904, "lon": 80.2014, "elev": 14.5, "capacity": 4.5},
    # Zone: North Chennai / Kosasthalaiyar
    {"id": "N010", "name": "Kosasthalaiyar Outfall", "type": "outfall",
     "lat": 13.1762, "lon": 80.2972, "elev": 0.5, "capacity": 90.0},
    {"id": "N011", "name": "Manali Junction", "type": "junction",
     "lat": 13.1673, "lon": 80.2629, "elev": 2.8, "capacity": 15.0},
    {"id": "N012", "name": "Tondiarpet Manhole", "type": "manhole",
     "lat": 13.1201, "lon": 80.2901, "elev": 3.5, "capacity": 9.0},
    # Zone: South Chennai / Pallavaram
    {"id": "N013", "name": "Pallavaram Outlet", "type": "outfall",
     "lat": 12.9675, "lon": 80.1494, "elev": 8.2, "capacity": 35.0},
    {"id": "N014", "name": "Chromepet Junction", "type": "junction",
     "lat": 12.9516, "lon": 80.1411, "elev": 10.1, "capacity": 11.0},
    {"id": "N015", "name": "Tambaram Storage", "type": "storage",
     "lat": 12.9249, "lon": 80.1000, "elev": 15.3, "capacity": 80.0},
    # Zone: Central Chennai (bottleneck-prone)
    {"id": "N016", "name": "Egmore Collector", "type": "junction",
     "lat": 13.0734, "lon": 80.2620, "elev": 6.9, "capacity": 8.0},
    {"id": "N017", "name": "Royapettah Manhole", "type": "manhole",
     "lat": 13.0524, "lon": 80.2638, "elev": 5.7, "capacity": 6.5},
    {"id": "N018", "name": "Mylapore Junction", "type": "junction",
     "lat": 13.0368, "lon": 80.2676, "elev": 4.9, "capacity": 9.0},
    {"id": "N019", "name": "Velachery Inlet", "type": "inlet",
     "lat": 12.9815, "lon": 80.2209, "elev": 8.8, "capacity": 5.0},
    {"id": "N020", "name": "Velachery Pump Station", "type": "pump",
     "lat": 12.9790, "lon": 80.2180, "elev": 8.1, "capacity": 40.0},
    # Additional nodes for network density
    {"id": "N021", "name": "T. Nagar Collector", "type": "junction",
     "lat": 13.0418, "lon": 80.2341, "elev": 7.2, "capacity": 10.5},
    {"id": "N022", "name": "Ashok Nagar Manhole", "type": "manhole",
     "lat": 13.0317, "lon": 80.2101, "elev": 9.1, "capacity": 7.8},
    {"id": "N023", "name": "KK Nagar Inlet", "type": "inlet",
     "lat": 13.0373, "lon": 80.1986, "elev": 11.4, "capacity": 4.0},
    {"id": "N024", "name": "Porur Lake Outfall", "type": "outfall",
     "lat": 13.0375, "lon": 80.1568, "elev": 12.7, "capacity": 50.0},
    {"id": "N025", "name": "Madipakkam Junction", "type": "junction",
     "lat": 12.9588, "lon": 80.1982, "elev": 9.3, "capacity": 8.5},
    {"id": "N026", "name": "Perungudi Manhole", "type": "manhole",
     "lat": 12.9632, "lon": 80.2302, "elev": 7.1, "capacity": 7.2},
    {"id": "N027", "name": "Sholinganallur Inlet", "type": "inlet",
     "lat": 12.9010, "lon": 80.2276, "elev": 5.8, "capacity": 5.5},
    {"id": "N028", "name": "Medavakkam Storage", "type": "storage",
     "lat": 12.9219, "lon": 80.1901, "elev": 10.2, "capacity": 60.0},
    {"id": "N029", "name": "Poonamallee Outlet", "type": "outfall",
     "lat": 13.0467, "lon": 80.1171, "elev": 18.5, "capacity": 40.0},
    {"id": "N030", "name": "Ambattur Junction", "type": "junction",
     "lat": 13.1147, "lon": 80.1596, "elev": 16.2, "capacity": 12.0},
]


def _make_provenance(model: str = "SyntheticRainfallProvider") -> DataProvenance:
    return DataProvenance(
        source=DataSourceType.SYNTHETIC_PROTOTYPE,
        provider=model,
        model_method="Synthetic time-series generation",
        model_version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        confidence=1.0,  # Confidence=1.0 because synthetic — known ground truth
        assumptions=[
            "SYNTHETIC DATA — NOT real observational data",
            "Generated for engineering prototype demonstration",
            "Replace provider with real IMD/AWS feed for production",
        ],
    )


# ── Synthetic Rainfall Provider ───────────────────────────────────────────────


class SyntheticRainfallProvider(RainfallProvider):
    """Generates physically-plausible synthetic rainfall for Chennai pilot.

    DATA SOURCE: SYNTHETIC_PROTOTYPE
    Rainfall intensities based on published IMD classification:
    - Light: < 7.5 mm/hr
    - Moderate: 7.5–35.4 mm/hr
    - Heavy: 35.5–64.4 mm/hr
    - Very Heavy: 64.5–115.5 mm/hr
    - Extreme: > 115.5 mm/hr
    """

    def __init__(self) -> None:
        self._base_intensity = 8.0  # mm/hr
        self._accumulated = 0.0
        self._scenario = "normal_rainfall"
        self._rng = random.Random(42)  # Reproducible seed

    def set_scenario(self, scenario: str, step_fraction: float = 0.0) -> None:
        """Update rainfall based on scenario and simulation progress."""
        self._scenario = scenario
        cfg = SCENARIOS.get(scenario, SCENARIOS["normal_rainfall"])
        peak = cfg["intensity_mm_hr"]
        # Ramp up: intensity increases over first 30% of simulation
        if step_fraction < 0.3:
            self._base_intensity = peak * (step_fraction / 0.3)
        elif step_fraction < 0.7:
            self._base_intensity = peak
        else:
            # Ramp down
            self._base_intensity = peak * (1.0 - (step_fraction - 0.7) / 0.3)
        self._accumulated += self._base_intensity / 60.0  # per minute increment

    @property
    def current_intensity(self) -> float:
        noise = self._rng.gauss(0, self._base_intensity * 0.05)
        return max(0.0, self._base_intensity + noise)

    async def get_current(self) -> RainfallObservation:
        intensity = self.current_intensity
        return RainfallObservation(
            timestamp=datetime.now(timezone.utc),
            latitude=13.0827,  # Chennai approximate centroid
            longitude=80.2707,
            intensity_mm_hr=round(intensity, 2),
            accumulated_mm=round(self._accumulated, 2),
            forecast_horizon_min=0,
            source=DataSourceType.SYNTHETIC_PROTOTYPE,
            quality_flag="SYNTHETIC",
            provenance=_make_provenance(),
        )

    async def get_forecast(self, hours: int = 3) -> List[RainfallObservation]:
        """Generate 15-minute interval forecasts using simple decay model."""
        forecasts = []
        now = datetime.now(timezone.utc)
        steps = hours * 4  # 15-min intervals

        cfg = SCENARIOS.get(self._scenario, SCENARIOS["normal_rainfall"])
        peak_intensity = cfg["intensity_mm_hr"]

        acc = self._accumulated
        for i in range(steps + 1):
            minutes = i * 15
            # Simple decay: intensity decreases after peak
            decay = math.exp(-0.008 * minutes)
            intensity = max(0.0, self._base_intensity * decay)
            acc += intensity * 0.25  # 15min = 0.25hr

            forecasts.append(RainfallObservation(
                timestamp=now + timedelta(minutes=minutes),
                latitude=13.0827,
                longitude=80.2707,
                intensity_mm_hr=round(intensity, 2),
                accumulated_mm=round(acc, 2),
                forecast_horizon_min=minutes,
                source=DataSourceType.SYNTHETIC_PROTOTYPE,
                quality_flag="SYNTHETIC_FORECAST",
                provenance=_make_provenance(
                    f"SyntheticForecastProvider (decay model, peak={peak_intensity}mm/hr)"
                ),
            ))

        return forecasts

    @property
    def provider_name(self) -> str:
        return "SyntheticRainfallProvider"

    @property
    def data_source_type(self) -> DataSourceType:
        return DataSourceType.SYNTHETIC_PROTOTYPE


# ── Synthetic Drainage Provider ───────────────────────────────────────────────


class SyntheticDrainageProvider(DrainageProvider):
    """Computes drainage network state from rainfall intensity.

    MODEL: Simplified linear capacity model
    ASSUMPTION: Flow ∝ (imperviousness × catchment_area × intensity)
    NOT a full hydraulic solver — SWMM integration path documented.
    DATA SOURCE: SYNTHETIC_PROTOTYPE
    """

    def __init__(self) -> None:
        # Catchment area (ha) per node — synthetic prototype values
        self._catchment_areas = {n["id"]: self._rng_area(n["elev"]) for n in CHENNAI_SYNTHETIC_NODES}
        self._blocked = set()

    def _rng_area(self, elev: float) -> float:
        """Estimate catchment area — lower elevation = larger contributing area."""
        base = max(5.0, 50.0 - elev * 2.5)
        return base * (0.8 + random.Random(int(elev * 100)).random() * 0.4)

    async def get_network_status(
        self, rainfall_mm_hr: float, scenario_modifier: float = 1.0
    ) -> DrainageNetworkStatus:
        """Estimate drainage state for given rainfall intensity.

        Flow estimation (simplified Rational Method):
          Q = C × I × A / 360
          C (runoff coefficient) ≈ 0.80 for urban impervious (synthetic)
          I = rainfall intensity (mm/hr)
          A = catchment area (ha)
          Q = flow rate (m³/s)
        """
        C = 0.80  # Urban imperviousness coefficient
        nodes = []
        surcharging = 0
        blocked = 0
        max_util = 0.0
        total_util = 0.0
        bottlenecks = []

        now = datetime.now(timezone.utc)

        for n in CHENNAI_SYNTHETIC_NODES:
            area = self._catchment_areas[n["id"]]
            capacity = n["capacity"] * scenario_modifier

            # Simplified inflow calculation
            Q_inflow = (C * rainfall_mm_hr * area) / 360.0

            # Apply some variance per node
            seed = hash(n["id"]) % 1000
            variance = 0.85 + (seed / 1000.0) * 0.30
            Q_inflow *= variance

            is_blocked = n["id"] in self._blocked
            if is_blocked:
                capacity *= 0.1  # Blocked = 10% effective capacity

            utilization = (Q_inflow / max(capacity, 0.01)) * 100.0
            is_surcharging = utilization > 100.0

            if is_surcharging:
                surcharging += 1
            if is_blocked:
                blocked += 1
            if utilization > 90.0:
                bottlenecks.append(n["id"])

            max_util = max(max_util, utilization)
            total_util += utilization

            # Risk level
            if utilization < 60:
                risk = RiskLevel.LOW
            elif utilization < 80:
                risk = RiskLevel.MODERATE
            elif utilization < 100:
                risk = RiskLevel.HIGH
            else:
                risk = RiskLevel.CRITICAL

            nodes.append(DrainageNodeStatus(
                node_id=n["id"],
                node_type=DrainageNodeType(n["type"]),
                latitude=n["lat"],
                longitude=n["lon"],
                elevation_m=n["elev"],
                capacity_m3_s=round(capacity, 3),
                current_flow_m3_s=round(Q_inflow, 3),
                utilization_pct=round(min(utilization, 200.0), 1),
                is_surcharging=is_surcharging,
                is_blocked=is_blocked,
                risk=risk,
                timestamp=now,
            ))

        avg_util = total_util / len(CHENNAI_SYNTHETIC_NODES)

        if max_util < 60:
            overall = RiskLevel.LOW
        elif max_util < 80:
            overall = RiskLevel.MODERATE
        elif max_util < 100:
            overall = RiskLevel.HIGH
        else:
            overall = RiskLevel.CRITICAL

        return DrainageNetworkStatus(
            timestamp=now,
            total_nodes=len(CHENNAI_SYNTHETIC_NODES),
            surcharging_nodes=surcharging,
            blocked_nodes=blocked,
            average_utilization_pct=round(avg_util, 1),
            max_utilization_pct=round(max_util, 1),
            bottleneck_nodes=bottlenecks[:5],
            overall_status=overall,
            nodes=nodes,
            provenance=DataProvenance(
                source=DataSourceType.SYNTHETIC_PROTOTYPE,
                provider="SyntheticDrainageProvider",
                model_method="Simplified Rational Method (Q = C×I×A/360)",
                model_version="1.0.0",
                timestamp=now,
                confidence=0.70,
                assumptions=[
                    "SYNTHETIC drainage network — not real CMWSSB data",
                    "C=0.80 (uniform urban imperviousness)",
                    "Linear flow-capacity model (not full hydraulic solver)",
                    "No pipe routing or backwater effects",
                ],
            ),
        )

    @property
    def provider_name(self) -> str:
        return "SyntheticDrainageProvider"


# ── Provider Registry ─────────────────────────────────────────────────────────

# Singletons
synthetic_rainfall = SyntheticRainfallProvider()
synthetic_drainage = SyntheticDrainageProvider()


def get_rainfall_provider(provider_name: str = "synthetic") -> RainfallProvider:
    if provider_name == "synthetic":
        return synthetic_rainfall
    raise ValueError(f"Unknown rainfall provider: {provider_name}")


def get_drainage_provider(provider_name: str = "synthetic") -> DrainageProvider:
    if provider_name == "synthetic":
        return synthetic_drainage
    raise ValueError(f"Unknown drainage provider: {provider_name}")
