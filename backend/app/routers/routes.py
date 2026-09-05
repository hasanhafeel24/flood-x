"""Routes router — GET /api/v1/routes/safe
GET /api/v1/routes/graph-info
"""
from fastapi import APIRouter, HTTPException
from app.schemas import SafeRoute, Coordinate, RiskLevel
from app.providers import synthetic_drainage, synthetic_rainfall
from app.services.routing.engine import road_graph

router = APIRouter()


@router.get("/routes/safe", response_model=SafeRoute)
async def get_safe_route(
    orig_lat: float = 13.0827,
    orig_lon: float = 80.2707,
    dest_lat: float = 12.9930,
    dest_lon: float = 80.1708,
    flood_aware: bool = True,
):
    """
    Get flood-aware route from origin to destination.

    DATA SOURCE: SYNTHETIC_PROTOTYPE road network.
    ALGORITHM: Dijkstra with flood-risk-weighted edges.
    Flood depths estimated from drainage utilization + rainfall intensity.
    """
    intensity = synthetic_rainfall.current_intensity
    drainage = await synthetic_drainage.get_network_status(intensity)

    origin = Coordinate(lat=orig_lat, lon=orig_lon)
    destination = Coordinate(lat=dest_lat, lon=dest_lon)

    route = road_graph.find_route(
        origin=origin,
        destination=destination,
        flood_aware=flood_aware,
        drainage_utilization_pct=drainage.average_utilization_pct,
        rainfall_intensity_mm_hr=intensity,
        overall_risk=drainage.overall_status,
    )

    if route is None:
        raise HTTPException(
            status_code=503,
            detail="No passable route found — all paths blocked by flooding",
        )

    return route


@router.get("/routes/graph-info")
async def get_graph_info():
    """Road graph metadata for transparency."""
    return {
        "data_source": "SYNTHETIC_PROTOTYPE",
        "note": "Synthetic road network — not real Chennai road data",
        "nodes": road_graph.node_count,
        "edges": road_graph.edge_count,
        "algorithm": "Dijkstra (NetworkX) with flood-risk edge weights",
        "flood_weight_multipliers": {
            "LOW": "1.0x (no penalty)",
            "MODERATE": "2.0x",
            "HIGH": "5.0x",
            "CRITICAL": "20.0x (effectively avoided)",
            "IMPASSABLE": "inf (depth > 50cm)",
        },
    }
