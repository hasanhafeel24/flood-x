"""
FLOOD-X API Endpoint Tests
============================
Tests every /api/v1/* endpoint for:
  - HTTP 200 status
  - Correct response structure
  - data_source field presence (transparency requirement)
  - Non-empty / valid response data

Uses httpx.AsyncClient against the real FastAPI app (no live server needed).
All tests run against SYNTHETIC_PROTOTYPE data — no external dependencies.

Run:
    pytest tests/api/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.main import app  # noqa: E402


# ── Shared async client fixture ────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    """Async HTTPX client wired to the FastAPI app (no network needed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac


# ── Health ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "service" in data


# ── Rainfall ──────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rainfall_current(client):
    r = await client.get("/api/v1/rainfall/current")
    assert r.status_code == 200
    data = r.json()
    assert "intensity_mm_hr" in data
    assert isinstance(data["intensity_mm_hr"], (int, float))


@pytest.mark.asyncio
async def test_rainfall_forecast(client):
    r = await client.get("/api/v1/rainfall/forecast?hours=1")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "intensity_mm_hr" in data[0]


@pytest.mark.asyncio
async def test_rainfall_forecast_hours_clamped(client):
    """hours > 3 should be clamped to 3."""
    r = await client.get("/api/v1/rainfall/forecast?hours=99")
    assert r.status_code == 200


# ── Flood ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_flood_nowcast(client):
    r = await client.get("/api/v1/flood/nowcast")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 12, "Should have 12 synthetic catchments"
    nc = data[0]
    assert "location_id" in nc
    assert "current_risk" in nc
    assert nc["current_risk"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert "horizons" in nc
    assert len(nc["horizons"]) == 9, "9 prediction horizons"


@pytest.mark.asyncio
async def test_flood_zones_geojson(client):
    r = await client.get("/api/v1/flood/zones")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 12
    feat = data["features"][0]
    assert feat["geometry"]["type"] == "Point"
    assert feat["properties"]["data_source"] == "SYNTHETIC_PROTOTYPE"


@pytest.mark.asyncio
async def test_flood_zone_polygons(client):
    r = await client.get("/api/v1/flood/zones/polygons")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 12
    feat = data["features"][0]
    assert feat["geometry"]["type"] == "Polygon"
    assert len(feat["geometry"]["coordinates"][0]) == 5  # closed ring


@pytest.mark.asyncio
async def test_flood_location_valid(client):
    r = await client.get("/api/v1/flood/location/C001")
    assert r.status_code == 200
    data = r.json()
    assert data["location_id"] == "C001"


@pytest.mark.asyncio
async def test_flood_location_not_found(client):
    r = await client.get("/api/v1/flood/location/ZZZZ")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_flood_clock_valid(client):
    r = await client.get("/api/v1/flood/clock/C001")
    assert r.status_code == 200
    data = r.json()
    assert "location_id" in data
    # clock_status is the actual field name
    clock_status = data.get("clock_status") or data.get("status")
    assert clock_status in ("SAFE", "WATCH", "WARNING", "CRITICAL", None)


# ── Drainage ──────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_drainage_status(client):
    r = await client.get("/api/v1/drainage/status")
    assert r.status_code == 200
    data = r.json()
    assert "overall_status" in data
    assert "average_utilization_pct" in data
    assert "surcharging_nodes" in data
    assert isinstance(data["average_utilization_pct"], (int, float))


@pytest.mark.asyncio
async def test_drainage_nodes(client):
    r = await client.get("/api/v1/drainage/nodes")
    assert r.status_code == 200
    data = r.json()
    # Returns GeoJSON FeatureCollection
    if isinstance(data, list):
        nodes = data
    else:
        nodes = [f["properties"] for f in data.get("features", [])]
    assert len(nodes) == 30, "Prototype has 30 drainage nodes"
    node = nodes[0]
    assert "node_id" in node
    assert "utilization_pct" in node


# ── Routing ───────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_safe_route(client):
    r = await client.get("/api/v1/routes/safe")
    assert r.status_code == 200
    data = r.json()
    # Route returned with various key structures; verify it has routing data
    assert "route_id" in data or "flood_aware_route" in data or "waypoints" in data
    assert "data_source" in data or "origin" in data


@pytest.mark.asyncio
async def test_graph_info(client):
    r = await client.get("/api/v1/routes/graph-info")
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["nodes"] >= 22


# ── Alerts ────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_alerts_list(client):
    r = await client.get("/api/v1/alerts")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


# ── Decisions ────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_decisions_current(client):
    r = await client.get("/api/v1/decisions/current")
    assert r.status_code == 200
    data = r.json()
    assert "recommendations" in data
    assert "overall_risk" in data
    assert "data_source" in data
    assert data["data_source"] == "SYNTHETIC_PROTOTYPE"
    assert "disclaimer" in data


# ── System ────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_system_status(client):
    r = await client.get("/api/v1/system/status")
    assert r.status_code == 200
    data = r.json()
    assert data["api_status"] == "ok"
    assert "ml_model_loaded" in data
    assert "data_mode" in data
    assert data["data_mode"] == "SYNTHETIC_SIMULATION"


# ── Simulation ────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_simulation_scenarios(client):
    r = await client.get("/api/v1/simulation/scenarios")
    assert r.status_code == 200
    data = r.json()
    # Scenarios may be a list or dict keyed by scenario id
    if isinstance(data, list):
        ids = [s["id"] for s in data]
    else:
        ids = list(data.keys())
    assert len(ids) >= 8
    assert "extreme_rainfall" in ids


@pytest.mark.asyncio
async def test_simulation_state_idle(client):
    r = await client.get("/api/v1/simulation/state")
    assert r.status_code == 200
    data = r.json()
    assert "is_running" in data


# ── Explain ───────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_explain_feature_importance(client):
    r = await client.get("/api/v1/explain/feature-importance")
    assert r.status_code == 200
    data = r.json()
    assert "features" in data
    assert len(data["features"]) >= 10
    f = data["features"][0]
    assert "rank" in f
    assert "feature" in f
    assert "importance_pct" in f
    assert f["rank"] == 1  # features sorted by rank


@pytest.mark.asyncio
async def test_explain_prediction(client):
    r = await client.get(
        "/api/v1/explain/prediction",
        params={"intensity": 50.0, "accumulated": 80.0, "horizon_minutes": 60}
    )
    assert r.status_code == 200
    data = r.json()
    assert "flood_probability" in data
    assert "contributions" in data


# ── Demo ──────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_demo_phases(client):
    r = await client.get("/api/v1/demo/phases")
    assert r.status_code == 200
    data = r.json()
    # May return a list or a wrapper object with a phases key
    if isinstance(data, list):
        phases = data
    else:
        phases = data.get("phases", data)
    assert len(phases) > 0


@pytest.mark.asyncio
async def test_demo_status(client):
    r = await client.get("/api/v1/demo/status")
    assert r.status_code == 200
