"""System status router — GET /api/v1/system/status"""
import time
from datetime import datetime, timezone
from fastapi import APIRouter
from app.simulation.engine import SimulationEngine
from app.schemas import SystemStatus
from app.core.config import settings
from app.services.ml.predictor import ml_predictor

router = APIRouter()
_start_time = time.time()

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status():
    engine = SimulationEngine.get_instance()
    warnings = ["Running in SYNTHETIC_SIMULATION mode — not real data"]
    if not ml_predictor.is_loaded:
        warnings.append("ML model not loaded — using rule-based fallback. Run: python scripts/train_models.py")

    return SystemStatus(
        timestamp=datetime.now(timezone.utc),
        api_status="ok",
        database_status="not_connected",  # DB not required for simulation mode
        rainfall_provider=settings.RAINFALL_PROVIDER,
        terrain_provider=settings.TERRAIN_PROVIDER,
        drainage_provider=settings.DRAINAGE_PROVIDER,
        ml_model_loaded=ml_predictor.is_loaded,
        ml_model_version=ml_predictor.model_version,
        simulation_active=engine.is_running,
        data_mode="SYNTHETIC_SIMULATION",
        uptime_seconds=round(time.time() - _start_time, 1),
        warnings=warnings,
    )

