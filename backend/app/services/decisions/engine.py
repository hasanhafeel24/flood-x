"""
FLOOD-X Decision Support Engine
=================================
Translates hydraulic state + ML nowcasts into structured, prioritised
decision recommendations for emergency operations centres.

METHODOLOGY (documented and transparent):
  1. Evaluate current state against decision thresholds
  2. Generate context-aware recommendations by action type
  3. Rank by impact × urgency matrix
  4. Return structured Recommendation objects with confidence + rationale

ALL recommendations are decision-support ONLY.
Not substitutes for official emergency management protocols.

DATA SOURCE: SYNTHETIC_PROTOTYPE inputs → MODELLED recommendations
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional

import structlog

from app.schemas import AlertSeverity, DrainageNetworkStatus, RiskLevel

log = structlog.get_logger(__name__)


# ── Decision Types ─────────────────────────────────────────────────────────────

class ActionCategory(str, Enum):
    DRAINAGE      = "drainage_operations"
    ROAD_CLOSURE  = "road_closure"
    EVACUATION    = "evacuation"
    PUMP_DEPLOY   = "pump_deployment"
    EMERGENCY_SVC = "emergency_services"
    PUBLIC_ALERT  = "public_alert"
    MONITORING    = "monitoring"
    RECOVERY      = "recovery"


class DecisionUrgency(str, Enum):
    IMMEDIATE  = "IMMEDIATE"   # Within 0–15 min
    HIGH       = "HIGH"        # Within 15–60 min
    MODERATE   = "MODERATE"    # Within 1–3 hours
    LOW        = "LOW"         # Monitoring / standby


@dataclass
class Recommendation:
    rec_id: str
    category: ActionCategory
    urgency: DecisionUrgency
    priority_rank: int                  # 1 = highest
    title: str
    rationale: str
    action_steps: List[str]
    target_locations: List[str]
    estimated_impact: str
    estimated_resources: str
    deadline_minutes: Optional[int]
    confidence: float                   # 0–1
    triggered_by: str                   # what condition triggered this
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_source: str = "SYNTHETIC_PROTOTYPE"
    disclaimer: str = "Decision-support only — not official emergency orders"


@dataclass
class DecisionPackage:
    """Full decision support package for the current hydraulic state."""
    package_id: str
    issued_at: datetime
    overall_risk: RiskLevel
    recommendations: List[Recommendation]
    situation_summary: str
    total_recommendations: int
    immediate_actions: int
    data_source: str = "SYNTHETIC_PROTOTYPE"
    disclaimer: str = "Decision-support only. Consult official emergency management protocols."


class DecisionSupportEngine:
    """
    Generates prioritised flood response recommendations.

    Thresholds and logic are fully documented — no black box decisions.
    All outputs include rationale, confidence, and explicit disclaimers.
    """

    # Drainage thresholds
    DRAIN_WATCH_PCT    = 80.0
    DRAIN_SURGE_PCT    = 100.0
    DRAIN_CRITICAL_PCT = 130.0

    # Rainfall thresholds (IMD classification mm/hr)
    RAIN_MODERATE = 7.5
    RAIN_HEAVY    = 35.5
    RAIN_VERY_HEAVY = 64.5
    RAIN_EXTREME  = 115.5

    # Flood depth thresholds (cm)
    DEPTH_WATCH    = 5.0
    DEPTH_WARNING  = 20.0
    DEPTH_CRITICAL = 45.0

    def generate(
        self,
        intensity_mm_hr: float,
        accumulated_mm: float,
        drainage: DrainageNetworkStatus,
        flooded_zones: int,
        total_zones: int,
        max_depth_cm: float,
        overall_risk: RiskLevel,
        scenario: str = "normal_rainfall",
    ) -> DecisionPackage:
        """Generate decision package for current hydraulic state."""
        now = datetime.now(timezone.utc)
        recs: List[Recommendation] = []

        # ── Rule 1: Public Alert Activation ───────────────────────────────────
        if intensity_mm_hr >= self.RAIN_HEAVY:
            urgency = (DecisionUrgency.IMMEDIATE if intensity_mm_hr >= self.RAIN_EXTREME
                       else DecisionUrgency.HIGH)
            recs.append(Recommendation(
                rec_id=f"REC-ALERT-{uuid.uuid4().hex[:6].upper()}",
                category=ActionCategory.PUBLIC_ALERT,
                urgency=urgency,
                priority_rank=1,
                title="Issue Public Flood Advisory",
                rationale=f"Rainfall intensity {intensity_mm_hr:.1f} mm/hr exceeds Heavy threshold ({self.RAIN_HEAVY} mm/hr). IMD classification requires immediate public notification.",
                action_steps=[
                    "Broadcast emergency SMS/cell broadcast to flood-prone zones",
                    "Update NDMA portal and state disaster management dashboard",
                    "Alert Chennai Corporation field officers",
                    "Coordinate with TANGEDCO for power safety measures",
                ],
                target_locations=["All Chennai districts", "Priority: Velachery, Adyar, Tambaram, Sholinganallur"],
                estimated_impact="Enables 100,000+ residents to take precautionary action",
                estimated_resources="Communication infrastructure (no physical resources required)",
                deadline_minutes=15 if urgency == DecisionUrgency.IMMEDIATE else 30,
                confidence=0.92,
                triggered_by=f"rainfall_intensity={intensity_mm_hr:.1f}mm/hr",
            ))

        # ── Rule 2: Drainage Maintenance Team Dispatch ─────────────────────────
        if drainage.surcharging_nodes > 0:
            n = drainage.surcharging_nodes
            urgency = (DecisionUrgency.IMMEDIATE if n > 8
                       else DecisionUrgency.HIGH if n > 4
                       else DecisionUrgency.MODERATE)
            recs.append(Recommendation(
                rec_id=f"REC-DRAIN-{uuid.uuid4().hex[:6].upper()}",
                category=ActionCategory.DRAINAGE,
                urgency=urgency,
                priority_rank=2,
                title=f"Deploy Drainage Maintenance to {n} Surcharging Nodes",
                rationale=f"{n} drainage nodes are surcharging (utilization > 100%). Surface flooding is imminent at these locations unless flow is restored.",
                action_steps=[
                    f"Dispatch {min(n, 5)} maintenance teams to bottleneck nodes: {', '.join(drainage.bottleneck_nodes[:3])}",
                    "Clear inlet grates and debris screens",
                    "Verify pump stations at outfall nodes are operational",
                    "Report status every 15 minutes to control room",
                ],
                target_locations=drainage.bottleneck_nodes[:5],
                estimated_impact=f"Restoring flow at bottleneck nodes can reduce surface flooding risk by 30–50%",
                estimated_resources=f"{min(n, 5)} maintenance teams, pump trucks",
                deadline_minutes=20,
                confidence=0.85,
                triggered_by=f"surcharging_nodes={n}",
            ))

        # ── Rule 3: Pump Deployment ────────────────────────────────────────────
        if drainage.max_utilization_pct > self.DRAIN_CRITICAL_PCT:
            recs.append(Recommendation(
                rec_id=f"REC-PUMP-{uuid.uuid4().hex[:6].upper()}",
                category=ActionCategory.PUMP_DEPLOY,
                urgency=DecisionUrgency.IMMEDIATE,
                priority_rank=2,
                title="Emergency Pump Deployment to Critical Bottlenecks",
                rationale=f"Drainage utilization reached {drainage.max_utilization_pct:.0f}% at peak node. Gravity drainage is overwhelmed — mechanical pumping required.",
                action_steps=[
                    f"Deploy mobile pumps to: {', '.join(drainage.bottleneck_nodes[:2])}",
                    "Target pump capacity: ≥ 0.5 m³/s per critical node",
                    "Ensure discharge location does not worsen downstream flooding",
                    "Monitor pump performance every 10 minutes",
                ],
                target_locations=drainage.bottleneck_nodes[:2],
                estimated_impact="Can reduce peak flood depth by 10–20 cm at critical locations",
                estimated_resources="2–4 mobile pump units, fuel supply, operator teams",
                deadline_minutes=30,
                confidence=0.88,
                triggered_by=f"max_utilization={drainage.max_utilization_pct:.0f}%",
            ))

        # ── Rule 4: Road Closure Advisory ─────────────────────────────────────
        if max_depth_cm > self.DEPTH_WARNING or flooded_zones > 2:
            recs.append(Recommendation(
                rec_id=f"REC-ROAD-{uuid.uuid4().hex[:6].upper()}",
                category=ActionCategory.ROAD_CLOSURE,
                urgency=DecisionUrgency.HIGH,
                priority_rank=3,
                title="Activate Flood-Aware Traffic Diversion",
                rationale=f"Predicted flood depth {max_depth_cm:.0f} cm exceeds safe driving threshold (20 cm). {flooded_zones} zones at HIGH/CRITICAL risk.",
                action_steps=[
                    "Activate variable message signs on Velachery Main Road, Adyar bridge approaches",
                    "Redirect traffic to OMR, ECR, and NH-16 bypass routes",
                    "Deploy traffic police at Adyar junction, Velachery flyover, Tambaram",
                    "Coordinate with Google Maps / Apple Maps via ITMS for real-time diversion",
                ],
                target_locations=["Velachery", "Adyar bridge", "Tambaram–Pallavaram road", "Sholinganallur junction"],
                estimated_impact="Prevents vehicle entrapment; reduces rescue demand",
                estimated_resources="Traffic police teams, VMS operators",
                deadline_minutes=45,
                confidence=0.80,
                triggered_by=f"max_depth={max_depth_cm:.0f}cm flooded_zones={flooded_zones}",
            ))

        # ── Rule 5: Emergency Services Pre-positioning ─────────────────────────
        if overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recs.append(Recommendation(
                rec_id=f"REC-EMRG-{uuid.uuid4().hex[:6].upper()}",
                category=ActionCategory.EMERGENCY_SVC,
                urgency=(DecisionUrgency.IMMEDIATE if overall_risk == RiskLevel.CRITICAL
                         else DecisionUrgency.HIGH),
                priority_rank=1,
                title="Pre-position Emergency Response Assets",
                rationale=f"Overall drainage risk is {overall_risk.value}. Historical data shows rescue demand increases sharply when risk exceeds HIGH.",
                action_steps=[
                    "Move NDRF/SDRF teams to forward staging areas near high-risk zones",
                    "Pre-position inflatable rescue boats at Adyar, Velachery, Tambaram",
                    "Alert hospitals in flood-prone zones (Fortis Malar, Apollo Vanagaram)",
                    "Activate State Emergency Operations Centre (SEOC) at full capacity",
                ],
                target_locations=["Adyar", "Velachery", "Tambaram", "Sholinganallur"],
                estimated_impact="Reduces rescue response time from 60–90 min to 15–25 min",
                estimated_resources="NDRF teams (2 companies), rescue boats (10+), SEOC staff",
                deadline_minutes=30 if overall_risk == RiskLevel.CRITICAL else 60,
                confidence=0.83,
                triggered_by=f"overall_risk={overall_risk.value}",
            ))

        # ── Rule 6: Evacuation Advisory ────────────────────────────────────────
        if max_depth_cm > self.DEPTH_CRITICAL or scenario in ["combined_extreme", "pump_failure"]:
            recs.append(Recommendation(
                rec_id=f"REC-EVAC-{uuid.uuid4().hex[:6].upper()}",
                category=ActionCategory.EVACUATION,
                urgency=DecisionUrgency.IMMEDIATE,
                priority_rank=1,
                title="Precautionary Evacuation Advisory for Low-Lying Areas",
                rationale=f"Predicted depth {max_depth_cm:.0f} cm exceeds critical threshold ({self.DEPTH_CRITICAL:.0f} cm). Occupants in ground-floor structures at risk.",
                action_steps=[
                    "Issue evacuation advisory for areas < 1m above MSL (Velachery, parts of Adyar)",
                    "Open relief camps: Corporation schools at Alandur, Guindy, Tambaram",
                    "Coordinate with Revenue Department for relief material pre-positioning",
                    "Prioritise vulnerable households: elderly, disabled, ground-floor residents",
                ],
                target_locations=["Velachery (elevation < 1m)", "Adyar riverbank areas", "Tambaram low-lying"],
                estimated_impact="Protects estimated 5,000–15,000 residents from inundation risk",
                estimated_resources="Transport buses, relief camps, revenue officers",
                deadline_minutes=20,
                confidence=0.75,  # Lower: evacuation is high-stakes, requires human verification
                triggered_by=f"max_depth={max_depth_cm:.0f}cm scenario={scenario}",
            ))

        # ── Rule 7: Monitoring (always present as baseline) ───────────────────
        recs.append(Recommendation(
            rec_id=f"REC-MON-{uuid.uuid4().hex[:6].upper()}",
            category=ActionCategory.MONITORING,
            urgency=DecisionUrgency.MODERATE,
            priority_rank=len(recs) + 1,
            title="Maintain Enhanced Drainage & Rainfall Monitoring",
            rationale="Continuous monitoring enables early detection of escalating conditions and supports adaptive decision-making.",
            action_steps=[
                "Refresh FLOOD-X nowcast every 15 minutes",
                "Field teams to report drainage levels at 30-minute intervals",
                "Monitor IMD forecast for next 6-hour outlook",
                "Track NDWI satellite imagery from Sentinel-2 (if available)",
            ],
            target_locations=["All monitoring stations"],
            estimated_impact="Early warning lead time: 30–90 minutes",
            estimated_resources="FLOOD-X system operators, field monitoring teams",
            deadline_minutes=None,
            confidence=0.95,
            triggered_by="continuous_monitoring_baseline",
        ))

        # Re-rank by urgency + priority
        urgency_order = {
            DecisionUrgency.IMMEDIATE: 0,
            DecisionUrgency.HIGH: 1,
            DecisionUrgency.MODERATE: 2,
            DecisionUrgency.LOW: 3,
        }
        recs.sort(key=lambda r: (urgency_order.get(r.urgency, 99), r.priority_rank))
        for i, r in enumerate(recs):
            r.priority_rank = i + 1

        immediate_count = sum(1 for r in recs if r.urgency == DecisionUrgency.IMMEDIATE)

        # Situation summary
        summary_parts = []
        if intensity_mm_hr > self.RAIN_EXTREME:
            summary_parts.append(f"EXTREME rainfall ({intensity_mm_hr:.0f} mm/hr)")
        elif intensity_mm_hr > self.RAIN_VERY_HEAVY:
            summary_parts.append(f"Very Heavy rainfall ({intensity_mm_hr:.0f} mm/hr)")
        elif intensity_mm_hr > self.RAIN_HEAVY:
            summary_parts.append(f"Heavy rainfall ({intensity_mm_hr:.0f} mm/hr)")
        if drainage.surcharging_nodes > 0:
            summary_parts.append(f"{drainage.surcharging_nodes} surcharging drainage nodes")
        if flooded_zones > 0:
            summary_parts.append(f"{flooded_zones}/{total_zones} zones at HIGH/CRITICAL risk")
        if max_depth_cm > self.DEPTH_WATCH:
            summary_parts.append(f"peak predicted depth {max_depth_cm:.0f} cm")

        situation = (
            f"Current situation: {'; '.join(summary_parts)}. "
            f"Overall system risk: {overall_risk.value}. "
            f"{len(recs)} recommendations generated, {immediate_count} requiring immediate action."
            if summary_parts else
            f"System normal. Monitoring active. Overall risk: {overall_risk.value}."
        )

        log.info(
            "decision_package_generated",
            risk=overall_risk.value,
            recommendations=len(recs),
            immediate=immediate_count,
        )

        return DecisionPackage(
            package_id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
            issued_at=now,
            overall_risk=overall_risk,
            recommendations=recs,
            situation_summary=situation,
            total_recommendations=len(recs),
            immediate_actions=immediate_count,
        )


# Singleton
decision_engine = DecisionSupportEngine()
