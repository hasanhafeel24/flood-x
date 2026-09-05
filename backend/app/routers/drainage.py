"""Drainage router — GET /api/v1/drainage/*"""
from fastapi import APIRouter
from app.providers import synthetic_drainage, synthetic_rainfall
from app.schemas import DrainageNetworkStatus

router = APIRouter()

@router.get("/drainage/status", response_model=DrainageNetworkStatus)
async def get_drainage_status():
    """Current drainage network status. DATA: SYNTHETIC_PROTOTYPE"""
    intensity = synthetic_rainfall.current_intensity
    return await synthetic_drainage.get_network_status(intensity)

@router.get("/drainage/nodes")
async def get_drainage_nodes():
    """All drainage nodes as GeoJSON. DATA: SYNTHETIC_PROTOTYPE"""
    status = await get_drainage_status()
    features = []
    for node in status.nodes:
        features.append({
            "type": "Feature",
            "properties": {
                "node_id": node.node_id,
                "node_type": node.node_type,
                "utilization_pct": node.utilization_pct,
                "is_surcharging": node.is_surcharging,
                "risk": node.risk,
                "capacity_m3_s": node.capacity_m3_s,
                "current_flow_m3_s": node.current_flow_m3_s,
                "data_source": "SYNTHETIC_PROTOTYPE",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [node.longitude, node.latitude],
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"data_source": "SYNTHETIC_PROTOTYPE"},
    }
