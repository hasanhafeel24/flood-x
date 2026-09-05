"""FLOOD-X Alert Engine — Generates alerts from system state."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from app.schemas import Alert, AlertSeverity, DrainageNetworkStatus, RiskLevel


class AlertEngine:
    """Rule-based alert generator.

    Converts hydraulic state into structured alerts for the dashboard.
    All alerts are decision-support — not official government orders.
    """

    def generate(
        self,
        intensity_mm_hr: float,
        drainage: DrainageNetworkStatus,
        step: int = 0,
    ) -> List[Alert]:
        alerts = []
        now = datetime.now(timezone.utc)

        # ── Rainfall alerts ──────────────────────────────────────────────────
        if intensity_mm_hr > 115:
            alerts.append(Alert(
                alert_id=f"RAIN-EXTREME-{step}",
                severity=AlertSeverity.EMERGENCY,
                title="Extreme Rainfall Event",
                description=f"Rainfall intensity {intensity_mm_hr:.1f} mm/hr exceeds extreme threshold (115 mm/hr).",
                latitude=13.0827, longitude=80.2707,
                location_name="Chennai Metro Area",
                issued_at=now,
                predicted_impact_time=now + timedelta(minutes=20),
                recommended_action="Activate emergency flood response. Close low-lying roads immediately.",
                confidence=0.90,
                source_model="Threshold Rule / IMD Classification",
            ))
        elif intensity_mm_hr > 64:
            alerts.append(Alert(
                alert_id=f"RAIN-HEAVY-{step}",
                severity=AlertSeverity.WARNING,
                title="Very Heavy Rainfall",
                description=f"Rainfall intensity {intensity_mm_hr:.1f} mm/hr — Very Heavy category (IMD).",
                latitude=13.0827, longitude=80.2707,
                location_name="Chennai Metro Area",
                issued_at=now,
                predicted_impact_time=now + timedelta(minutes=40),
                recommended_action="Monitor drainage. Alert field teams. Prepare pump deployment.",
                confidence=0.88,
                source_model="Threshold Rule / IMD Classification",
            ))
        elif intensity_mm_hr > 35:
            alerts.append(Alert(
                alert_id=f"RAIN-MOD-{step}",
                severity=AlertSeverity.WATCH,
                title="Heavy Rainfall Watch",
                description=f"Rainfall intensity {intensity_mm_hr:.1f} mm/hr — Heavy category (IMD).",
                latitude=13.0827, longitude=80.2707,
                location_name="Chennai Metro Area",
                issued_at=now,
                predicted_impact_time=None,
                recommended_action="Monitor drainage utilization. No immediate action required.",
                confidence=0.85,
                source_model="Threshold Rule / IMD Classification",
            ))

        # ── Drainage surcharge alerts ────────────────────────────────────────
        if drainage.surcharging_nodes > 5:
            alerts.append(Alert(
                alert_id=f"DRAIN-SURGE-{step}",
                severity=AlertSeverity.WARNING,
                title="Multiple Drainage Nodes Surcharging",
                description=f"{drainage.surcharging_nodes} drainage nodes exceeded capacity. Surface flooding likely.",
                latitude=13.0178, longitude=80.2534,
                location_name="Multiple Locations",
                issued_at=now,
                predicted_impact_time=now + timedelta(minutes=15),
                recommended_action="Deploy maintenance teams to bottleneck nodes. Monitor road flooding.",
                confidence=0.82,
                source_model="Drainage State Monitor",
            ))

        if drainage.max_utilization_pct > 150:
            for node_id in drainage.bottleneck_nodes[:2]:
                alerts.append(Alert(
                    alert_id=f"BOTTLENECK-{node_id}-{step}",
                    severity=AlertSeverity.EMERGENCY,
                    title=f"Critical Bottleneck: {node_id}",
                    description=f"Node {node_id} utilization {drainage.max_utilization_pct:.0f}% — overflow imminent.",
                    latitude=13.0178, longitude=80.2534,
                    location_name=f"Node {node_id}",
                    issued_at=now,
                    predicted_impact_time=now + timedelta(minutes=10),
                    recommended_action="Emergency pump deployment. Immediate road closure advisory.",
                    confidence=0.88,
                    source_model="Drainage Bottleneck Detector",
                ))

        return alerts


alert_engine = AlertEngine()
