"""Initial tables — FloodEvent, AlertLog, SimulationRun

Revision ID: 0001
Revises:
Create Date: 2026-09-06 08:50:00.000000

Creates the three core FLOOD-X tables.
These are prototype tables; real production deployment should add
PostGIS geometry columns for spatial queries (see DEPLOYMENT_GUIDE.md).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ─────────────────────────────────────────────────────────────────
    risk_level_enum = sa.Enum(
        "LOW", "MODERATE", "HIGH", "CRITICAL",
        name="risk_level_enum"
    )
    alert_severity_enum = sa.Enum(
        "INFO", "WATCH", "WARNING", "EMERGENCY",
        name="alert_severity_enum"
    )

    # ── flood_events ──────────────────────────────────────────────────────────
    op.create_table(
        "flood_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location_id", sa.String(10), nullable=False),
        sa.Column("location_name", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon_minutes", sa.Integer(), nullable=False),
        sa.Column("flood_probability", sa.Float(), nullable=False),
        sa.Column("estimated_depth_cm", sa.Float(), nullable=False),
        sa.Column("current_risk", risk_level_enum, nullable=False),
        sa.Column("rainfall_intensity_mm_hr", sa.Float(), nullable=True),
        sa.Column("drainage_utilization_pct", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False),
        sa.Column("run_id", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flood_events_location_id", "flood_events", ["location_id"])
    op.create_index("ix_flood_events_run_id",      "flood_events", ["run_id"])
    op.create_index("ix_flood_events_recorded_at", "flood_events", ["recorded_at"])

    # ── alert_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "alert_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alert_id", sa.String(50), nullable=False),
        sa.Column("severity", alert_severity_enum, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location_name", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False),
        sa.Column("run_id", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alert_id"),
    )
    op.create_index("ix_alert_logs_alert_id", "alert_logs", ["alert_id"])
    op.create_index("ix_alert_logs_run_id",   "alert_logs", ["run_id"])

    # ── simulation_runs ───────────────────────────────────────────────────────
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(50), nullable=False),
        sa.Column("scenario", sa.String(100), nullable=False),
        sa.Column("speed", sa.Float(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=False),
        sa.Column("peak_rainfall_mm_hr", sa.Float(), nullable=True),
        sa.Column("peak_drainage_util_pct", sa.Float(), nullable=True),
        sa.Column("flooded_zones_count", sa.Integer(), nullable=True),
        sa.Column("total_alerts_issued", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("data_source", sa.String(50), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_simulation_runs_run_id", "simulation_runs", ["run_id"])


def downgrade() -> None:
    op.drop_table("simulation_runs")
    op.drop_table("alert_logs")
    op.drop_table("flood_events")
    op.execute("DROP TYPE IF EXISTS alert_severity_enum")
    op.execute("DROP TYPE IF EXISTS risk_level_enum")
