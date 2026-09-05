"""Demo router — POST /api/v1/demo/start, GET /api/v1/demo/status, POST /api/v1/demo/reset"""
from fastapi import APIRouter
from app.services.demo.orchestrator import demo_orchestrator, DEMO_PHASES

router = APIRouter()


@router.post("/demo/start")
async def start_demo():
    """
    Start the deterministic SIH demo scenario.

    Runs 8 phases of the Chennai extreme rainfall event (seed=42).
    Results are identical on every run for judge consistency.
    DATA SOURCE: SYNTHETIC_PROTOTYPE
    """
    status = await demo_orchestrator.start()
    return {
        "message": "Demo started",
        "phases": [
            {
                "phase": i + 1,
                "name": p.name,
                "description": p.description,
                "key_observation": p.key_observation,
                "expected_risk": p.expected_risk,
            }
            for i, p in enumerate(DEMO_PHASES)
        ],
        "data_source": "SYNTHETIC_PROTOTYPE",
        "note": "Deterministic scenario — seed=42. Identical results on every run.",
    }


@router.get("/demo/status")
async def get_demo_status():
    """Current demo phase and progress."""
    s = demo_orchestrator.status
    return {
        "is_running": s.is_running,
        "current_phase": s.current_phase_idx + 1,
        "current_phase_name": s.current_phase_name,
        "total_phases": s.total_phases,
        "key_observation": s.key_observation,
        "expected_risk": s.expected_risk,
        "elapsed_seconds": round(s.elapsed_seconds, 1),
        "data_source": "SYNTHETIC_PROTOTYPE",
    }


@router.post("/demo/reset")
async def reset_demo():
    """Reset demo to phase 1."""
    await demo_orchestrator.reset()
    return {"message": "Demo reset"}


@router.get("/demo/phases")
async def list_demo_phases():
    """Full demo phase manifest for SIH judges."""
    return {
        "total_phases": len(DEMO_PHASES),
        "estimated_duration_minutes": sum(p.duration_steps * 2.5 / 60 for p in DEMO_PHASES),
        "phases": [
            {
                "phase": i + 1,
                "name": p.name,
                "description": p.description,
                "scenario": p.scenario,
                "intensity_target_mm_hr": p.intensity_target,
                "key_observation": p.key_observation,
                "expected_risk": p.expected_risk,
            }
            for i, p in enumerate(DEMO_PHASES)
        ],
        "data_source": "SYNTHETIC_PROTOTYPE",
        "note": "Modelled on 2015 Chennai floods. Not real observed data.",
    }
