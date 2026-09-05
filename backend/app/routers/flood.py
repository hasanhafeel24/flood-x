"""Flood router — GET /api/v1/flood/*"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.services.nowcast.engine import nowcast_engine
from app.schemas import LocationNowcast, FloodClock

router = APIRouter()

# Catchment bounding boxes (SYNTHETIC_PROTOTYPE — approximate extents for pilot)
CATCHMENT_POLYGONS = [
    {"id": "C001", "name": "Velachery Basin",    "bbox": [80.19, 12.97, 80.24, 13.00]},
    {"id": "C002", "name": "Adyar Corridor",     "bbox": [80.22, 13.00, 80.27, 13.03]},
    {"id": "C003", "name": "T. Nagar Basin",     "bbox": [80.22, 13.03, 80.27, 13.06]},
    {"id": "C004", "name": "Tambaram Sub-basin", "bbox": [80.09, 12.91, 80.14, 12.95]},
    {"id": "C005", "name": "Sholinganallur",     "bbox": [80.21, 12.88, 80.26, 12.93]},
    {"id": "C006", "name": "Porur Lake Basin",   "bbox": [80.14, 13.02, 80.19, 13.06]},
    {"id": "C007", "name": "Chromepet Basin",    "bbox": [80.12, 12.94, 80.17, 12.97]},
    {"id": "C008", "name": "Perungudi Basin",    "bbox": [80.23, 12.94, 80.28, 12.98]},
    {"id": "C009", "name": "Mylapore Basin",     "bbox": [80.25, 13.03, 80.29, 13.06]},
    {"id": "C010", "name": "Ambattur Basin",     "bbox": [80.12, 13.09, 80.17, 13.13]},
    {"id": "C011", "name": "Pallavaram Basin",   "bbox": [80.12, 12.95, 80.17, 12.99]},
    {"id": "C012", "name": "KK Nagar Basin",     "bbox": [80.19, 13.03, 80.22, 13.06]},
]

@router.get("/flood/nowcast", response_model=List[LocationNowcast])
async def get_nowcast():
    """0–3 hour flood nowcast for all pilot locations."""
    return await nowcast_engine.generate_nowcasts()

@router.get("/flood/zones")
async def get_flood_zones():
    """Current flood risk zones (GeoJSON Points). DATA: SYNTHETIC_PROTOTYPE"""
    nowcasts = await nowcast_engine.generate_nowcasts()
    nc_map = {nc.location_id: nc for nc in nowcasts}
    features = []
    for nc in nowcasts:
        features.append({
            "type": "Feature",
            "properties": {
                "location_id": nc.location_id,
                "location_name": nc.location_name,
                "risk": nc.current_risk,
                "depth_cm": nc.current_depth_cm,
                "prob_60min": next(
                    (h.flood_probability for h in nc.horizons if h.horizon_minutes == 60),
                    0.0,
                ),
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

@router.get("/flood/zones/polygons")
async def get_flood_zone_polygons():
    """
    Flood risk zones as GeoJSON Polygons (catchment bounding boxes).
    DATA SOURCE: SYNTHETIC_PROTOTYPE — approximate extents, not surveyed boundaries.
    """
    nowcasts = await nowcast_engine.generate_nowcasts()
    nc_list = list(nowcasts)
    features = []
    for i, cp in enumerate(CATCHMENT_POLYGONS):
        nc = nc_list[i] if i < len(nc_list) else None
        risk  = nc.current_risk if nc else "LOW"
        depth = nc.current_depth_cm if nc else 0.0
        w, s, e, n = cp["bbox"]
        features.append({
            "type": "Feature",
            "properties": {
                "location_id": cp["id"],
                "location_name": cp["name"],
                "risk": risk,
                "depth_cm": depth,
                "data_source": "SYNTHETIC_PROTOTYPE",
                "note": "Approximate bounding box — not surveyed catchment boundary",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[w,s],[e,s],[e,n],[w,n],[w,s]]],
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "data_source": "SYNTHETIC_PROTOTYPE",
            "coordinate_system": "WGS84",
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
