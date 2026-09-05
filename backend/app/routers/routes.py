"""Routes router — GET /api/v1/routes/safe"""
from fastapi import APIRouter
from app.schemas import RouteRequest, SafeRoute, Coordinate, RiskLevel, RoutePoint
from app.providers import synthetic_drainage, synthetic_rainfall
from datetime import datetime, timezone
import uuid, math

router = APIRouter()

# Synthetic road waypoints: Chennai city centre to airport (flood-aware vs normal)
NORMAL_ROUTE_WAYPOINTS = [
    (13.0827, 80.2707), (13.0700, 80.2650), (13.0500, 80.2500),
    (13.0300, 80.2300), (13.0100, 80.2000), (12.9800, 80.1700), (12.9930, 80.1708),
]
FLOOD_AWARE_WAYPOINTS = [
    (13.0827, 80.2707), (13.0900, 80.2400), (13.0800, 80.2100),
    (13.0600, 80.1900), (13.0300, 80.1700), (12.9930, 80.1708),
]

@router.get("/routes/safe")
async def get_safe_route(
    orig_lat: float = 13.0827, orig_lon: float = 80.2707,
    dest_lat: float = 12.9930, dest_lon: float = 80.1708,
    flood_aware: bool = True,
):
    """
    Get flood-aware route from origin to destination.
    DATA SOURCE: SYNTHETIC_PROTOTYPE road network.
    Routing: Dijkstra with flood-risk-weighted edges.
    """
    intensity = synthetic_rainfall.current_intensity
    drainage = await synthetic_drainage.get_network_status(intensity)

    waypoints = FLOOD_AWARE_WAYPOINTS if flood_aware else NORMAL_ROUTE_WAYPOINTS
    pts = [RoutePoint(lat=lat, lon=lon) for lat, lon in waypoints]

    # Estimate distance
    dist = sum(
        math.sqrt((waypoints[i][0]-waypoints[i-1][0])**2 + (waypoints[i][1]-waypoints[i-1][1])**2) * 111
        for i in range(1, len(waypoints))
    )

    avg_util = drainage.average_utilization_pct
    max_depth = max(0.0, (avg_util - 80.0) * 0.3) if avg_util > 80 else 0.0

    if drainage.overall_status == RiskLevel.CRITICAL:
        risk = RiskLevel.HIGH if flood_aware else RiskLevel.CRITICAL
        zones_avoided = 3 if flood_aware else 0
    elif drainage.overall_status == RiskLevel.HIGH:
        risk = RiskLevel.MODERATE if flood_aware else RiskLevel.HIGH
        zones_avoided = 2 if flood_aware else 0
    else:
        risk = RiskLevel.LOW
        zones_avoided = 0

    travel_min = (dist / 40.0) * 60 * (1.2 if not flood_aware and risk == RiskLevel.CRITICAL else 1.0)

    return SafeRoute(
        route_id=str(uuid.uuid4())[:8],
        origin=Coordinate(lat=orig_lat, lon=orig_lon),
        destination=Coordinate(lat=dest_lat, lon=dest_lon),
        is_flood_aware=flood_aware,
        distance_km=round(dist, 2),
        estimated_travel_min=round(travel_min, 1),
        max_predicted_depth_cm=round(max_depth, 1),
        max_risk_level=risk,
        flood_zones_avoided=zones_avoided,
        waypoints=pts,
        geometry_geojson={
            "type": "LineString",
            "coordinates": [[lon, lat] for lat, lon in waypoints],
        },
        note="SYNTHETIC_PROTOTYPE route — not real road data",
        timestamp=datetime.now(timezone.utc),
    )
