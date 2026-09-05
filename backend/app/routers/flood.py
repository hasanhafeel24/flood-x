"""Flood router — GET /api/v1/flood/*"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.services.nowcast.engine import nowcast_engine
from app.schemas import LocationNowcast, FloodClock

router = APIRouter()

@router.get("/flood/nowcast", response_model=List[LocationNowcast])
async def get_nowcast():
    """0–3 hour flood nowcast for all pilot locations."""
    return await nowcast_engine.generate_nowcasts()

@router.get("/flood/zones")
async def get_flood_zones():
    """Current flood risk zones (GeoJSON). DATA: SYNTHETIC_PROTOTYPE"""
    nowcasts = await nowcast_engine.generate_nowcasts()
    features = []
    for nc in nowcasts:
        features.append({
            "type": "Feature",
            "properties": {
                "location_id": nc.location_id,
                "location_name": nc.location_name,
                "risk": nc.current_risk,
                "depth_cm": nc.current_depth_cm,
                "data_source": "SYNTHETIC_PROTOTYPE",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [nc.longitude, nc.latitude],
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "data_source": "SYNTHETIC_PROTOTYPE",
            "note": "Prototype data — not real flood observations",
        },
    }

@router.get("/flood/location/{location_id}", response_model=LocationNowcast)
async def get_location_nowcast(location_id: str):
    """Detailed nowcast for a specific location."""
    nowcasts = await nowcast_engine.generate_nowcasts()
    nc = next((n for n in nowcasts if n.location_id == location_id), None)
    if not nc:
        raise HTTPException(404, detail=f"Location {location_id} not found")
    return nc

@router.get("/flood/clock/{location_id}", response_model=FloodClock)
async def get_flood_clock(location_id: str):
    """Flood Clock for a specific location — time-to-critical prediction."""
    clock = await nowcast_engine.get_flood_clock(location_id)
    if not clock:
        raise HTTPException(404, detail=f"Location {location_id} not found")
    return clock
