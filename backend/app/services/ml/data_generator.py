"""
FLOOD-X ML Training Data Generator
====================================
DATA SOURCE: SYNTHETIC_PROTOTYPE
Generates physically-consistent training samples by running the
hydrology + drainage pipeline across a wide parameter sweep.

This produces labelled data for:
  - XGBoost Classifier: flood_occurred (binary)
  - XGBoost Regressor:  flood_depth_cm (continuous)

Feature engineering mirrors what the live nowcast engine computes,
so the trained model can be plugged in directly.

IMPORTANT: Model trained on synthetic data. Real-event validation
required before operational deployment.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, fields
from typing import List

import structlog

log = structlog.get_logger(__name__)

# ── Feature schema ─────────────────────────────────────────────────────────────
# Keep in sync with inference features in nowcast/engine.py

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


@dataclass
class TrainingSample:
    # Features
    rainfall_intensity_mm_hr: float
    rainfall_duration_hr: float
    accumulated_rainfall_mm: float
    drainage_utilization_pct: float
    drainage_surcharging_nodes: int
    catchment_imperviousness: float
    catchment_cn: int
    catchment_area_ha: float
    terrain_elevation_m: float
    terrain_slope_pct: float
    terrain_susceptibility: float
    antecedent_moisture_mm: float
    time_since_last_rain_hr: float
    horizon_minutes: int

    # Labels
    flood_occurred: int        # 0 or 1
    flood_depth_cm: float      # 0.0+
    risk_level_int: int        # 0=LOW, 1=MOD, 2=HIGH, 3=CRITICAL

    def to_feature_list(self) -> List[float]:
        return [
            self.rainfall_intensity_mm_hr,
            self.rainfall_duration_hr,
            self.accumulated_rainfall_mm,
            self.drainage_utilization_pct,
            float(self.drainage_surcharging_nodes),
            self.catchment_imperviousness,
            float(self.catchment_cn),
            self.catchment_area_ha,
            self.terrain_elevation_m,
            self.terrain_slope_pct,
            self.terrain_susceptibility,
            self.antecedent_moisture_mm,
            self.time_since_last_rain_hr,
            float(self.horizon_minutes),
        ]


def _scs_rainfall_excess(rainfall_mm: float, cn: int, antecedent_mm: float = 0.0) -> float:
    if antecedent_mm > 50:
        cn = min(99, int(cn * 1.10))
    elif antecedent_mm < 12:
        cn = max(1, int(cn * 0.90))
    S = (25400.0 / cn) - 254.0
    Ia = 0.2 * S
    if rainfall_mm <= Ia:
        return 0.0
    return ((rainfall_mm - Ia) ** 2) / (rainfall_mm - Ia + S)


def _compute_labels(
    intensity: float,
    duration_hr: float,
    cn: int,
    imperviousness: float,
    area_ha: float,
    drainage_util: float,
    elevation: float,
    antecedent: float,
    horizon_min: int,
) -> tuple[int, float, int]:
    """Compute physically-based flood labels from parameters."""

    rainfall_mm = intensity * duration_hr
    Pe = _scs_rainfall_excess(rainfall_mm, cn, antecedent)

    # Surface ponding depth estimate
    f_cap = max(0, (1.0 - imperviousness) * 15.0)
    surface_mm = max(0.0, (intensity - f_cap) * duration_hr)
    depth_cm = (Pe * 0.15 + surface_mm * 0.8)

    # Drainage overwhelm contribution
    if drainage_util > 100:
        depth_cm += (drainage_util - 100) * 0.08

    # Low-lying locations flood more
    elevation_factor = max(0.5, 1.0 - elevation * 0.02)
    depth_cm *= elevation_factor

    # Future horizon: depth has inertia
    decay = math.exp(-0.004 * horizon_min)
    depth_cm = max(0.0, depth_cm * (1.0 + (1 - decay) * 0.3))

    depth_cm = max(0.0, round(depth_cm, 2))
    flooded = 1 if depth_cm > 5.0 else 0

    if depth_cm < 5:
        risk = 0
    elif depth_cm < 20:
        risk = 1
    elif depth_cm < 45:
        risk = 2
    else:
        risk = 3

    return flooded, depth_cm, risk


def generate_training_data(n_samples: int = 8000, seed: int = 42) -> List[TrainingSample]:
    """
    Generate N synthetic training samples by sweeping:
    - 8 scenario types
    - 12 catchment parameter sets
    - 9 forecast horizons
    - Random antecedent conditions

    Returns a list of TrainingSample with deterministic seed.
    """
    rng = random.Random(seed)
    samples = []

    # Parameter ranges (physically realistic for Chennai)
    intensity_configs = [
        (2.0, 8.0, "light"),
        (8.0, 35.0, "moderate"),
        (35.0, 64.0, "heavy"),
        (64.0, 115.0, "very_heavy"),
        (115.0, 180.0, "extreme"),
        (5.0, 20.0, "prolonged_light"),
        (20.0, 45.0, "prolonged_mod"),
        (80.0, 130.0, "cloudburst"),
    ]

    cn_range = list(range(72, 93, 2))
    imperv_range = [0.52, 0.60, 0.68, 0.72, 0.75, 0.80, 0.82, 0.88, 0.92]
    area_range = [480.0, 620.0, 780.0, 890.0, 950.0, 1100.0, 1200.0, 1400.0, 1650.0, 1850.0, 2100.0, 2200.0]
    elevation_range = [0.5, 1.2, 2.8, 4.1, 5.2, 6.9, 7.4, 8.8, 10.2, 12.3, 14.5, 16.2, 18.5]
    horizons = [0, 15, 30, 45, 60, 90, 120, 150, 180]

    attempts = 0
    while len(samples) < n_samples and attempts < n_samples * 5:
        attempts += 1

        cfg = rng.choice(intensity_configs)
        intensity = rng.uniform(cfg[0], cfg[1])
        duration = rng.uniform(0.25, 8.0)
        acc = intensity * duration * rng.uniform(0.4, 1.0)
        cn = rng.choice(cn_range)
        imperv = rng.choice(imperv_range) + rng.uniform(-0.05, 0.05)
        imperv = max(0.4, min(0.98, imperv))
        area = rng.choice(area_range)
        elev = rng.choice(elevation_range) + rng.uniform(-0.5, 0.5)
        elev = max(0.3, elev)
        slope = rng.uniform(0.1, 8.0)
        susceptibility = max(0.0, min(1.0, 1.0 - elev / 20.0 + rng.gauss(0, 0.05)))
        antecedent = rng.uniform(0.0, 80.0)
        time_since = rng.uniform(0.0, 72.0)
        drain_util = rng.uniform(20.0, 200.0)
        surcharging = max(0, int((drain_util - 100) / 10)) if drain_util > 100 else 0
        horizon = rng.choice(horizons)

        flooded, depth, risk = _compute_labels(
            intensity, duration, cn, imperv, area,
            drain_util, elev, antecedent, horizon,
        )

        samples.append(TrainingSample(
            rainfall_intensity_mm_hr=round(intensity, 2),
            rainfall_duration_hr=round(duration, 3),
            accumulated_rainfall_mm=round(acc, 2),
            drainage_utilization_pct=round(drain_util, 1),
            drainage_surcharging_nodes=surcharging,
            catchment_imperviousness=round(imperv, 3),
            catchment_cn=cn,
            catchment_area_ha=round(area, 1),
            terrain_elevation_m=round(elev, 2),
            terrain_slope_pct=round(slope, 2),
            terrain_susceptibility=round(susceptibility, 3),
            antecedent_moisture_mm=round(antecedent, 2),
            time_since_last_rain_hr=round(time_since, 2),
            horizon_minutes=horizon,
            flood_occurred=flooded,
            flood_depth_cm=depth,
            risk_level_int=risk,
        ))

    log.info(
        "training_data_generated",
        total=len(samples),
        flooded=sum(s.flood_occurred for s in samples),
        pct_flooded=round(sum(s.flood_occurred for s in samples) / len(samples) * 100, 1),
    )
    return samples
