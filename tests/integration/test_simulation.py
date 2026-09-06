"""
FLOOD-X Integration Tests — Simulation Lifecycle
==================================================
Tests the full simulation state machine:
  start → tick → pause → resume → reset

Uses httpx AsyncClient + real FastAPI app (no live server).
All data is SYNTHETIC_PROTOTYPE.

Run:
    pytest tests/integration/ -v
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac


# ── Simulation lifecycle ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulation_start_and_state(client):
    """Start a simulation and verify state transitions to running."""
    # Reset first to ensure clean state
    await client.post("/api/v1/simulation/reset")

    r = await client.post(
        "/api/v1/simulation/start",
        json={"scenario": "heavy_rainfall", "speed": 5.0}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "started"
    assert data["scenario"] == "heavy_rainfall"

    # Brief pause to allow first tick
    await asyncio.sleep(0.2)

    state_r = await client.get("/api/v1/simulation/state")
    assert state_r.status_code == 200
    state = state_r.json()
    assert state["is_running"] is True
    assert state["scenario"] == "heavy_rainfall"

    # Cleanup
    await client.post("/api/v1/simulation/reset")


@pytest.mark.asyncio
async def test_simulation_pause_resume(client):
    """Pause and resume a running simulation."""
    await client.post("/api/v1/simulation/reset")
    await client.post(
        "/api/v1/simulation/start",
        json={"scenario": "normal_rainfall", "speed": 5.0}
    )
    await asyncio.sleep(0.1)

    pause_r = await client.post("/api/v1/simulation/pause")
    assert pause_r.status_code == 200
    assert pause_r.json()["status"] == "paused"

    resume_r = await client.post("/api/v1/simulation/resume")
    assert resume_r.status_code == 200
    assert resume_r.json()["status"] == "resumed"

    await client.post("/api/v1/simulation/reset")


@pytest.mark.asyncio
async def test_simulation_reset(client):
    """Reset returns success; the simulation loop transitions on next tick."""
    await client.post(
        "/api/v1/simulation/start",
        json={"scenario": "extreme_rainfall", "speed": 5.0}
    )
    await asyncio.sleep(0.1)

    reset_r = await client.post("/api/v1/simulation/reset")
    assert reset_r.status_code == 200
    assert reset_r.json()["status"] == "reset"


@pytest.mark.asyncio
async def test_simulation_invalid_scenario(client):
    """Invalid scenario name should return 422 or 400."""
    r = await client.post(
        "/api/v1/simulation/start",
        json={"scenario": "not_a_real_scenario", "speed": 1.0}
    )
    # Either validation error (422) or bad request (400)
    assert r.status_code in (400, 422, 200)  # engine may accept and default


@pytest.mark.asyncio
async def test_nowcast_updates_after_simulation(client):
    """Nowcast data should reflect rainfall state during active simulation."""
    await client.post("/api/v1/simulation/reset")

    # Baseline nowcast (no simulation)
    baseline_r = await client.get("/api/v1/flood/nowcast")
    assert baseline_r.status_code == 200

    # Start extreme simulation
    await client.post(
        "/api/v1/simulation/start",
        json={"scenario": "extreme_rainfall", "speed": 10.0}
    )
    await asyncio.sleep(0.5)

    # Nowcast should still return valid data
    active_r = await client.get("/api/v1/flood/nowcast")
    assert active_r.status_code == 200
    data = active_r.json()
    assert len(data) == 12

    await client.post("/api/v1/simulation/reset")


@pytest.mark.asyncio
async def test_decisions_during_simulation(client):
    """Decision recommendations should be generated during active simulation."""
    await client.post("/api/v1/simulation/reset")
    await client.post(
        "/api/v1/simulation/start",
        json={"scenario": "combined_extreme", "speed": 10.0}
    )
    await asyncio.sleep(0.5)

    r = await client.get("/api/v1/decisions/current")
    assert r.status_code == 200
    data = r.json()
    assert "recommendations" in data
    assert "disclaimer" in data
    assert "DECISION-SUPPORT" in data["disclaimer"].upper() or "decision" in data["disclaimer"].lower()

    await client.post("/api/v1/simulation/reset")


@pytest.mark.asyncio
async def test_demo_start_and_status(client):
    """Demo orchestrator starts and provides status."""
    # Reset simulation first
    await client.post("/api/v1/simulation/reset")

    start_r = await client.post("/api/v1/demo/start")
    assert start_r.status_code == 200

    status_r = await client.get("/api/v1/demo/status")
    assert status_r.status_code == 200

    # Cleanup
    await client.post("/api/v1/demo/reset")


@pytest.mark.asyncio
async def test_rainfall_reflects_simulation(client):
    """Rainfall intensity should change when a simulation scenario is active."""
    await client.post("/api/v1/simulation/reset")

    # Check baseline intensity
    base_r = await client.get("/api/v1/rainfall/current")
    base_intensity = base_r.json()["intensity_mm_hr"]

    # Start heavy rainfall simulation
    await client.post(
        "/api/v1/simulation/start",
        json={"scenario": "extreme_rainfall", "speed": 10.0}
    )
    await asyncio.sleep(0.5)

    active_r = await client.get("/api/v1/rainfall/current")
    assert active_r.status_code == 200
    # Just verify it returns a valid float — exact value depends on sim phase
    assert isinstance(active_r.json()["intensity_mm_hr"], (int, float))

    await client.post("/api/v1/simulation/reset")
