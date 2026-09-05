"""
FLOOD-X Hydrology Engine — Rainfall to Runoff
=============================================
MODEL: SCS Curve Number (CN) + Rational Method
DATA: SYNTHETIC_PROTOTYPE inputs
ASSUMPTIONS: Documented below

Physical basis:
  - SCS-CN method: USDA-NRCS standard for urban runoff estimation
  - Rational Method: Q_peak = C × I × A / 360
  - Time of concentration: Kirpich (1940) formula
  - All parameters estimated from synthetic land-cover data

Limitations:
  - Assumes spatially uniform rainfall over catchment
  - No distributed routing
  - Simplified antecedent moisture condition (AMC II)
  - NOT validated against real Chennai flood events
  This is a prototype model for demonstration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

import structlog

log = structlog.get_logger(__name__)

# ── Chennai Synthetic Catchments ──────────────────────────────────────────────
# 12 catchments covering key urban zones
# SOURCE: SYNTHETIC_PROTOTYPE — not real CMWSSB/NRSC delineation

SYNTHETIC_CATCHMENTS: List[Dict] = [
    {
        "id": "C001", "name": "Adyar Upper Catchment",
        "area_ha": 1850.0, "cn": 85, "tc_min": 45.0,
        "centroid_lat": 13.0250, "centroid_lon": 80.2100,
        "imperviousness": 0.75, "drainage_node": "N004",
    },
    {
        "id": "C002", "name": "Adyar Lower Catchment",
        "area_ha": 1200.0, "cn": 88, "tc_min": 30.0,
        "centroid_lat": 13.0150, "centroid_lon": 80.2450,
        "imperviousness": 0.82, "drainage_node": "N003",
    },
    {
        "id": "C003", "name": "Cooum Catchment",
        "area_ha": 2100.0, "cn": 84, "tc_min": 55.0,
        "centroid_lat": 13.0827, "centroid_lon": 80.2350,
        "imperviousness": 0.72, "drainage_node": "N007",
    },
    {
        "id": "C004", "name": "North Chennai Catchment",
        "area_ha": 950.0, "cn": 80, "tc_min": 35.0,
        "centroid_lat": 13.1400, "centroid_lon": 80.2700,
        "imperviousness": 0.68, "drainage_node": "N011",
    },
    {
        "id": "C005", "name": "Velachery Basin",
        "area_ha": 1400.0, "cn": 87, "tc_min": 40.0,
        "centroid_lat": 12.9815, "centroid_lon": 80.2180,
        "imperviousness": 0.80, "drainage_node": "N019",
    },
    {
        "id": "C006", "name": "Pallavaram Catchment",
        "area_ha": 780.0, "cn": 78, "tc_min": 50.0,
        "centroid_lat": 12.9600, "centroid_lon": 80.1450,
        "imperviousness": 0.62, "drainage_node": "N014",
    },
    {
        "id": "C007", "name": "T. Nagar / Mambalam",
        "area_ha": 620.0, "cn": 90, "tc_min": 25.0,
        "centroid_lat": 13.0400, "centroid_lon": 80.2300,
        "imperviousness": 0.88, "drainage_node": "N021",
    },
    {
        "id": "C008", "name": "Anna Nagar Catchment",
        "area_ha": 890.0, "cn": 83, "tc_min": 38.0,
        "centroid_lat": 13.0850, "centroid_lon": 80.2100,
        "imperviousness": 0.73, "drainage_node": "N008",
    },
    {
        "id": "C009", "name": "Ambattur Industrial",
        "area_ha": 1100.0, "cn": 76, "tc_min": 60.0,
        "centroid_lat": 13.1100, "centroid_lon": 80.1600,
        "imperviousness": 0.60, "drainage_node": "N030",
    },
    {
        "id": "C010", "name": "Sholinganallur Catchment",
        "area_ha": 1650.0, "cn": 82, "tc_min": 45.0,
        "centroid_lat": 12.9010, "centroid_lon": 80.2250,
        "imperviousness": 0.70, "drainage_node": "N027",
    },
    {
        "id": "C011", "name": "Central Chennai Dense",
        "area_ha": 480.0, "cn": 92, "tc_min": 20.0,
        "centroid_lat": 13.0734, "centroid_lon": 80.2620,
        "imperviousness": 0.92, "drainage_node": "N016",
    },
    {
        "id": "C012", "name": "Porur Wetlands Fringe",
        "area_ha": 2200.0, "cn": 72, "tc_min": 70.0,
        "centroid_lat": 13.0350, "centroid_lon": 80.1600,
        "imperviousness": 0.52, "drainage_node": "N024",
    },
]


@dataclass
class RunoffResult:
    """Output of runoff calculation for one catchment and one time step."""
    catchment_id: str
    catchment_name: str
    drainage_node: str
    rainfall_mm_hr: float
    rainfall_excess_mm: float    # SCS-CN effective rainfall
    runoff_volume_m3: float      # Total runoff volume
    peak_flow_m3_s: float        # Rational Method peak flow
    surface_accumulation_mm: float  # Water depth on surface
    time_to_concentration_min: float
    is_overland_flow: bool       # True when inflow exceeds drainage capacity


class HydrologyEngine:
    """
    Rainfall-to-Runoff engine implementing SCS-CN and Rational Method.

    Scientific basis:
    ─────────────────
    SCS Curve Number (CN):
      S  = (25400/CN) - 254           [potential maximum retention, mm]
      Ia = 0.2 × S                    [initial abstraction]
      Pe = (P - Ia)² / (P - Ia + S)  [rainfall excess, mm]  if P > Ia else 0

    Rational Method (peak flow):
      Q = C × I × A / 360             [m³/s]
      C: runoff coefficient ≈ imperviousness
      I: rainfall intensity [mm/hr]
      A: catchment area [ha]

    Time of concentration (Kirpich, 1940):
      Tc = 0.0195 × (L^0.77) × (S^-0.385)
      L: flow path length [m] (estimated from area)
      S: slope [m/m] (assumed 0.005 average urban)

    Limitations documented in docs/HYDROLOGY_MODEL.md
    """

    def __init__(self) -> None:
        self._antecedent_moisture: Dict[str, float] = {
            c["id"]: 0.0 for c in SYNTHETIC_CATCHMENTS
        }

    def _scs_rainfall_excess(
        self, rainfall_mm: float, cn: int, antecedent_mm: float = 0.0
    ) -> float:
        """Calculate rainfall excess using SCS-CN method.

        Args:
            rainfall_mm: Rainfall depth for the time step (mm)
            cn: SCS Curve Number (dimensionless)
            antecedent_mm: Prior accumulated rainfall (affects AMC)

        Returns:
            Rainfall excess (effective rainfall) in mm
        """
        # Antecedent moisture condition: adjust CN
        if antecedent_mm > 50:
            # AMC III (wet) — increase CN
            cn_adj = min(99, int(cn * 1.10))
        elif antecedent_mm < 12:
            # AMC I (dry) — decrease CN
            cn_adj = max(1, int(cn * 0.90))
        else:
            cn_adj = cn  # AMC II (normal)

        S = (25400.0 / cn_adj) - 254.0  # Potential maximum retention (mm)
        Ia = 0.2 * S                     # Initial abstraction (mm)

        if rainfall_mm <= Ia:
            return 0.0

        Pe = ((rainfall_mm - Ia) ** 2) / (rainfall_mm - Ia + S)
        return max(0.0, Pe)

    def _time_of_concentration(
        self, area_ha: float, slope: float = 0.005
    ) -> float:
        """Kirpich formula for time of concentration (minutes).

        L (flow path) estimated as: L ≈ √(area × 10000) × 1.5 [m]
        """
        L = math.sqrt(area_ha * 10000) * 1.5  # metres
        Tc = 0.0195 * (L ** 0.77) * (slope ** -0.385)
        return max(5.0, Tc)

    def calculate_runoff(
        self,
        rainfall_intensity_mm_hr: float,
        duration_min: float = 15.0,
        accumulated_mm: float = 0.0,
    ) -> List[RunoffResult]:
        """
        Calculate runoff for all catchments given current rainfall.

        Args:
            rainfall_intensity_mm_hr: Current intensity (mm/hr)
            duration_min: Duration of this time step (minutes)
            accumulated_mm: Total accumulated rainfall so far (mm)

        Returns:
            List of RunoffResult for each catchment
        """
        results = []
        rainfall_mm = rainfall_intensity_mm_hr * (duration_min / 60.0)

        for cat in SYNTHETIC_CATCHMENTS:
            # Update antecedent moisture
            self._antecedent_moisture[cat["id"]] += rainfall_mm * 0.3  # simplified

            Pe = self._scs_rainfall_excess(
                rainfall_mm,
                cat["cn"],
                self._antecedent_moisture[cat["id"]],
            )

            # Runoff volume (m³)
            area_m2 = cat["area_ha"] * 10000.0
            Q_vol = (Pe / 1000.0) * area_m2  # m³

            # Peak flow — Rational Method
            C = cat["imperviousness"]
            Q_peak = (C * rainfall_intensity_mm_hr * cat["area_ha"]) / 360.0  # m³/s

            # Tc
            Tc = self._time_of_concentration(cat["area_ha"])

            # Surface accumulation estimate
            # If intensity > infiltration capacity, water ponds on surface
            f_capacity = max(0, (1.0 - cat["imperviousness"]) * 15.0)  # mm/hr
            surface_acc = max(0.0, rainfall_intensity_mm_hr - f_capacity) * (duration_min / 60.0)

            results.append(RunoffResult(
                catchment_id=cat["id"],
                catchment_name=cat["name"],
                drainage_node=cat["drainage_node"],
                rainfall_mm_hr=rainfall_intensity_mm_hr,
                rainfall_excess_mm=round(Pe, 3),
                runoff_volume_m3=round(Q_vol, 2),
                peak_flow_m3_s=round(Q_peak, 4),
                surface_accumulation_mm=round(surface_acc, 3),
                time_to_concentration_min=round(Tc, 1),
                is_overland_flow=Q_peak > 0.5,  # Simplified threshold
            ))

        return results

    def reset_antecedent_moisture(self) -> None:
        """Reset antecedent moisture to dry conditions (AMC I)."""
        self._antecedent_moisture = {c["id"]: 0.0 for c in SYNTHETIC_CATCHMENTS}


# Singleton
hydrology_engine = HydrologyEngine()
