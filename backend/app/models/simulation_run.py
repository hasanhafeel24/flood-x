"""
SimulationRun ORM Model
========================
Records each simulation run for reproducibility, comparison,
and provenance tracking.

Stores: scenario, start/end time, peak metrics, run config.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, JSON
from app.core.database import Base


class SimulationRun(Base):
    """
    One row per simulation execution.

    Columns:
        id              — auto PK
        run_id          — UUID (matches run_id in FloodEvent + AlertLog)
        scenario        — scenario name (e.g. 'extreme_rainfall')
        speed           — playback speed multiplier
        started_at      — UTC start time
        ended_at        — UTC end time (NULL if still running / crashed)
        total_steps     — total simulation steps executed
        peak_rainfall_mm_hr     — peak intensity observed
        peak_drainage_util_pct  — peak drainage utilisation
        flooded_zones_count     — max concurrent flooded zones
        total_alerts_issued     — total alerts generated
        completed       — True if ran to natural end
        data_source     — SYNTHETIC_PROTOTYPE
        config          — JSON blob of full run config for reproducibility
    """
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), nullable=False, unique=True, index=True)

    scenario = Column(String(100), nullable=False)
    speed = Column(Float, nullable=False, default=1.0)

    started_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_steps = Column(Integer, nullable=False, default=0)

    # Peak metrics for retrospective analysis
    peak_rainfall_mm_hr = Column(Float, nullable=True)
    peak_drainage_util_pct = Column(Float, nullable=True)
    flooded_zones_count = Column(Integer, nullable=True)
    total_alerts_issued = Column(Integer, nullable=True, default=0)

    completed = Column(Boolean, nullable=False, default=False)

    # Provenance
    data_source = Column(String(50), nullable=False, default="SYNTHETIC_PROTOTYPE")
    config = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SimulationRun {self.run_id} "
            f"scenario={self.scenario} "
            f"steps={self.total_steps}>"
        )
