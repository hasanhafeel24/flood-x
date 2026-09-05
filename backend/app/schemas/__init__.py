"""FLOOD-X Pydantic Schemas — Shared types and base models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WATCH = "WATCH"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"


class DrainageNodeType(str, Enum):
    INLET = "inlet"
    JUNCTION = "junction"
    MANHOLE = "manhole"
    PUMP = "pump"
    STORAGE = "storage"
    OUTFALL = "outfall"


class SimulationScenario(str, Enum):
    NORMAL = "normal_rainfall"
    HEAVY = "heavy_rainfall"
    EXTREME = "extreme_rainfall"
    SHORT_INTENSE = "short_intense_storm"
    PROLONGED = "prolonged_rainfall"
    DRAINAGE_BLOCKAGE = "drainage_blockage"
    PUMP_FAILURE = "pump_failure"
    COMBINED_EXTREME = "combined_extreme"


class DataSourceType(str, Enum):
    REAL = "REAL"
    SIMULATED = "SIMULATED"
    MODELLED = "MODELLED"
    SYNTHETIC_PROTOTYPE = "SYNTHETIC_PROTOTYPE"
    ASSUMED = "ASSUMED"


class FloodClockStatus(str, Enum):
    SAFE = "SAFE"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ── Provenance ────────────────────────────────────────────────────────────────

class DataProvenance(BaseModel):
    """Transparency record — every prediction exposes its data lineage."""
    source: DataSourceType
    provider: str
    model_method: str
    model_version: str
    timestamp: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    resolution: Optional[str] = None
    assumptions: Optional[List[str]] = None


# ── Coordinates ───────────────────────────────────────────────────────────────

class Coordinate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class BoundingBox(BaseModel):
    west: float
    south: float
    east: float
    north: float


# ── Rainfall ──────────────────────────────────────────────────────────────────

class RainfallObservation(BaseModel):
    timestamp: datetime
    latitude: float
    longitude: float
    intensity_mm_hr: float = Field(ge=0, description="Rainfall intensity (mm/hr)")
    accumulated_mm: float = Field(ge=0, description="Accumulated rainfall (mm)")
    forecast_horizon_min: int = Field(ge=0, description="Minutes ahead (0 = current)")
    source: DataSourceType
    quality_flag: str = "OK"
    provenance: DataProvenance


# ── Drainage ──────────────────────────────────────────────────────────────────

class DrainageNodeStatus(BaseModel):
    node_id: str
    node_type: DrainageNodeType
    latitude: float
    longitude: float
    elevation_m: float
    capacity_m3_s: float
    current_flow_m3_s: float
    utilization_pct: float = Field(ge=0, le=200, description="Can exceed 100% (surcharge)")
    is_surcharging: bool
    is_blocked: bool
    risk: RiskLevel
    timestamp: datetime


class DrainageNetworkStatus(BaseModel):
    timestamp: datetime
    total_nodes: int
    surcharging_nodes: int
    blocked_nodes: int
    average_utilization_pct: float
    max_utilization_pct: float
    bottleneck_nodes: List[str]
    overall_status: RiskLevel
    nodes: List[DrainageNodeStatus]
    provenance: DataProvenance


# ── Flood Prediction ──────────────────────────────────────────────────────────

class NowcastHorizon(BaseModel):
    horizon_minutes: int
    forecast_time: datetime
    flood_probability: float = Field(ge=0.0, le=1.0)
    estimated_depth_cm: float = Field(ge=0.0)
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)


class LocationNowcast(BaseModel):
    location_id: str
    location_name: str
    latitude: float
    longitude: float
    current_risk: RiskLevel
    current_depth_cm: float
    horizons: List[NowcastHorizon]  # T+0 to T+180
    provenance: DataProvenance


class FloodZone(BaseModel):
    zone_id: str
    name: str
    risk_level: RiskLevel
    estimated_depth_cm: float
    flood_probability: float
    area_km2: float
    affected_population_estimate: Optional[int] = None
    geometry_geojson: Dict[str, Any]  # GeoJSON polygon
    timestamp: datetime


# ── Flood Clock ───────────────────────────────────────────────────────────────

class FloodClockEntry(BaseModel):
    status: FloodClockStatus
    minutes_from_now: int
    estimated_depth_cm: float
    flood_probability: float


class FloodClock(BaseModel):
    location_id: str
    location_name: str
    latitude: float
    longitude: float
    current_status: FloodClockStatus
    time_to_watch_min: Optional[int] = None
    time_to_warning_min: Optional[int] = None
    time_to_critical_min: Optional[int] = None
    estimated_peak_depth_cm: float
    confidence: float
    timeline: List[FloodClockEntry]
    last_updated: datetime
    provenance: DataProvenance


# ── Routing ───────────────────────────────────────────────────────────────────

class RoutePoint(BaseModel):
    lat: float
    lon: float


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    avoid_flood_risk: bool = True


class SafeRoute(BaseModel):
    route_id: str
    origin: Coordinate
    destination: Coordinate
    is_flood_aware: bool
    distance_km: float
    estimated_travel_min: float
    max_predicted_depth_cm: float
    max_risk_level: RiskLevel
    flood_zones_avoided: int
    waypoints: List[RoutePoint]
    geometry_geojson: Dict[str, Any]
    note: str
    timestamp: datetime


# ── Alerts ────────────────────────────────────────────────────────────────────

class Alert(BaseModel):
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    latitude: float
    longitude: float
    location_name: str
    issued_at: datetime
    predicted_impact_time: Optional[datetime] = None
    recommended_action: str
    status: str = "ACTIVE"
    confidence: float
    source_model: str


# ── Decision Support ──────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    rec_id: str
    category: str  # road_closure | pump_deployment | evacuation | warning | monitoring
    severity: AlertSeverity
    location_name: str
    latitude: float
    longitude: float
    reason: str
    predicted_time: Optional[datetime] = None
    confidence: float
    recommended_action: str
    priority_rank: int
    timestamp: datetime
    disclaimer: str = (
        "This is a decision-support suggestion, not an official government order."
    )


# ── Simulation ────────────────────────────────────────────────────────────────

class SimulationState(BaseModel):
    run_id: str
    scenario: SimulationScenario
    is_running: bool
    is_paused: bool
    elapsed_seconds: float
    simulated_time: datetime
    rainfall_intensity_mm_hr: float
    step: int
    total_steps: int
    phase_label: str


class SimulationControl(BaseModel):
    scenario: SimulationScenario = SimulationScenario.NORMAL
    speed_multiplier: float = Field(default=1.0, ge=0.1, le=10.0)


# ── System ────────────────────────────────────────────────────────────────────

class SystemStatus(BaseModel):
    timestamp: datetime
    api_status: str
    database_status: str
    rainfall_provider: str
    terrain_provider: str
    drainage_provider: str
    ml_model_loaded: bool
    ml_model_version: str
    simulation_active: bool
    data_mode: str = "SYNTHETIC_SIMULATION"
    uptime_seconds: float
    warnings: List[str] = []
