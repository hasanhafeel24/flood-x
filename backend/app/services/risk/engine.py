"""
FLOOD-X Risk Engine
===================
Converts hydraulic state + ML predictions into transparent risk levels.

METHODOLOGY (documented):
  Risk Score = weighted sum of:
    - Predicted flood probability (w=0.35)
    - Drainage utilization (w=0.25)
    - Predicted depth score (w=0.20)
    - Rainfall intensity score (w=0.12)
    - Terrain susceptibility (w=0.08)

Risk levels:
  LOW:      score < 0.30
  MODERATE: 0.30 ≤ score < 0.55
  HIGH:     0.55 ≤ score < 0.80
  CRITICAL: score ≥ 0.80
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from app.schemas import RiskLevel


@dataclass
class RiskInput:
    location_id: str
    flood_probability: float      # 0–1
    drainage_utilization_pct: float  # 0–200+
    predicted_depth_cm: float      # 0–150+
    rainfall_intensity_mm_hr: float
    terrain_susceptibility: float  # 0–1 (from DEM analysis)
    road_importance: float = 0.5   # 0–1


@dataclass
class RiskOutput:
    location_id: str
    risk_score: float
    risk_level: RiskLevel
    component_scores: Dict[str, float]
    dominant_factor: str


class RiskEngine:
    """
    Transparent flood risk scoring engine.

    Weights and thresholds are documented and configurable.
    This is a rule-based + weighted scoring system — not a black box.
    """

    # Component weights (must sum to 1.0)
    WEIGHTS = {
        "flood_probability": 0.35,
        "drainage_utilization": 0.25,
        "depth": 0.20,
        "rainfall_intensity": 0.12,
        "terrain_susceptibility": 0.08,
    }

    # Risk thresholds
    THRESHOLDS = {
        RiskLevel.LOW: 0.0,
        RiskLevel.MODERATE: 0.30,
        RiskLevel.HIGH: 0.55,
        RiskLevel.CRITICAL: 0.80,
    }

    def score(self, inp: RiskInput) -> RiskOutput:
        """Compute risk score and level for a location."""

        # Normalise each component to 0–1
        prob_score = max(0.0, min(1.0, inp.flood_probability))

        # Drainage: 100% = full = 0.5, 150% = surcharge = 0.85
        drain_score = min(1.0, inp.drainage_utilization_pct / 150.0)

        # Depth: 0cm=0, 30cm=0.5, 60cm=0.8, 100cm+=1.0
        depth_score = min(1.0, 1.0 - math.exp(-inp.predicted_depth_cm / 40.0))

        # Rainfall: 0=0, 50mm/hr=0.6, 100mm/hr=0.9, 150+=1.0
        rain_score = min(1.0, 1.0 - math.exp(-inp.rainfall_intensity_mm_hr / 60.0))

        # Terrain: pass-through
        terrain_score = max(0.0, min(1.0, inp.terrain_susceptibility))

        components = {
            "flood_probability": prob_score,
            "drainage_utilization": drain_score,
            "depth": depth_score,
            "rainfall_intensity": rain_score,
            "terrain_susceptibility": terrain_score,
        }

        # Weighted sum
        score = sum(
            components[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )

        # Clamp
        score = max(0.0, min(1.0, score))

        # Level
        level = RiskLevel.LOW
        for lvl, threshold in sorted(self.THRESHOLDS.items(), key=lambda x: x[1]):
            if score >= threshold:
                level = lvl

        # Dominant factor (highest weighted contribution)
        weighted_contributions = {
            k: components[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        }
        dominant = max(weighted_contributions, key=weighted_contributions.get)

        return RiskOutput(
            location_id=inp.location_id,
            risk_score=round(score, 4),
            risk_level=level,
            component_scores={k: round(v, 4) for k, v in components.items()},
            dominant_factor=dominant,
        )

    def score_many(self, inputs: List[RiskInput]) -> List[RiskOutput]:
        return [self.score(inp) for inp in inputs]


# Singleton
risk_engine = RiskEngine()
