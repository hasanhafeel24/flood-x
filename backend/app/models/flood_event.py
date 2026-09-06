"""
FloodEvent ORM Model
=====================
Records individual flood prediction events for each location-horizon.
Intended for post-event analysis and model validation when real data arrives.

DATA SOURCE: SYNTHETIC_PROTOTYPE in current deployment.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text
from sqlalchemy import Enum as SAEnum
import enum

from app.core.database import Base


class RiskLevelEnum(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FloodEvent(Base):
    """
    Stores one nowcast prediction per location per horizon per simulation tick.

    Columns:
        id              — auto PK
        location_id     — catchment ID (C001–C012)
        location_name   — human-readable name
        latitude        — WGS84
        longitude       — WGS84
        recorded_at     — UTC timestamp of prediction
        horizon_minutes — forecast horizon (0, 15, 30 … 180)
        flood_probability — ML classifier output [0.0–1.0]
        estimated_depth_cm — ML regressor output
        current_risk    — derived risk level
        rainfall_intensity_mm_hr — input feature at prediction time
        drainage_utilization_pct — input feature
        data_source     — always SYNTHETIC_PROTOTYPE in prototype
        run_id          — simulation run this event belongs to
    """
    __tablename__ = "flood_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(String(10), nullable=False, index=True)
    location_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    recorded_at = Column(DateTime(timezone=True), nullable=False,
                         default=lambda: datetime.now(timezone.utc))
    horizon_minutes = Column(Integer, nullable=False, default=0)

    flood_probability = Column(Float, nullable=False, default=0.0)
    estimated_depth_cm = Column(Float, nullable=False, default=0.0)
    current_risk = Column(
        SAEnum(RiskLevelEnum, name="risk_level_enum"),
        nullable=False,
        default=RiskLevelEnum.LOW,
    )

    # Input features stored for traceability
    rainfall_intensity_mm_hr = Column(Float, nullable=True)
    drainage_utilization_pct = Column(Float, nullable=True)

    # Provenance
    data_source = Column(String(50), nullable=False, default="SYNTHETIC_PROTOTYPE")
    run_id = Column(String(50), nullable=True, index=True)

    def __repr__(self) -> str:
        return (
            f"<FloodEvent loc={self.location_id} "
            f"t+{self.horizon_minutes}min "
            f"risk={self.current_risk} "
            f"depth={self.estimated_depth_cm:.1f}cm>"
        )
