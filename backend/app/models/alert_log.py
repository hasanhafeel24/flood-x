"""
AlertLog ORM Model
===================
Persists generated alerts for audit trail, escalation tracking,
and retrospective analysis.

All alerts in prototype are SYNTHETIC — labelled on every row.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text
from sqlalchemy import Enum as SAEnum
import enum

from app.core.database import Base


class AlertSeverityEnum(str, enum.Enum):
    INFO = "INFO"
    WATCH = "WATCH"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"


class AlertLog(Base):
    """
    Persisted alert record. One row per alert issued by the AlertEngine.

    Columns:
        id              — auto PK
        alert_id        — UUID from AlertEngine (business key)
        severity        — INFO / WATCH / WARNING / EMERGENCY
        title           — short alert title
        description     — full alert description
        location_name   — affected area name
        latitude        — WGS84
        longitude       — WGS84
        issued_at       — UTC timestamp
        expires_at      — optional expiry (NULL = no expiry)
        recommended_action — decision-support text
        confidence      — [0.0–1.0] alert confidence
        acknowledged    — whether an operator acknowledged it
        acknowledged_at — when acknowledged
        data_source     — SYNTHETIC_PROTOTYPE
        run_id          — simulation run that generated this alert
    """
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(50), nullable=False, unique=True, index=True)

    severity = Column(
        SAEnum(AlertSeverityEnum, name="alert_severity_enum"),
        nullable=False,
        default=AlertSeverityEnum.INFO,
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location_name = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    issued_at = Column(DateTime(timezone=True), nullable=False,
                       default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    recommended_action = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.5)

    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    # Provenance
    data_source = Column(String(50), nullable=False, default="SYNTHETIC_PROTOTYPE")
    run_id = Column(String(50), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<AlertLog {self.alert_id} sev={self.severity} loc={self.location_name}>"
