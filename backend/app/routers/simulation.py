"""Simulation router — POST /api/v1/simulation/*"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.simulation.engine import SimulationEngine
from app.schemas import SimulationControl, SimulationState
from typing import Optional

router = APIRouter()

class StartRequest(BaseModel):
    scenario: str = "normal_rainfall"
    speed: float = Field(default=1.0, ge=0.1, le=10.0)

@router.post("/simulation/start")
async def start_simulation(req: StartRequest):
    """Start a simulation scenario."""
    engine = SimulationEngine.get_instance()
    await engine.start(scenario=req.scenario, speed=req.speed)
    return {"status": "started", "scenario": req.scenario, "speed": req.speed}

@router.post("/simulation/pause")
async def pause_simulation():
    engine = SimulationEngine.get_instance()
    await engine.pause()
    return {"status": "paused"}

@router.post("/simulation/resume")
async def resume_simulation():
    engine = SimulationEngine.get_instance()
    await engine.resume()
    return {"status": "resumed"}

@router.post("/simulation/reset")
async def reset_simulation():
    engine = SimulationEngine.get_instance()
    await engine.reset()
    return {"status": "reset"}

@router.get("/simulation/state")
async def get_simulation_state():
    engine = SimulationEngine.get_instance()
    state = engine.current_state
    if not state:
        return {"is_running": False, "message": "No active simulation"}
    return state

@router.get("/simulation/scenarios")
async def get_scenarios():
    from app.providers import SCENARIOS
    return SCENARIOS
