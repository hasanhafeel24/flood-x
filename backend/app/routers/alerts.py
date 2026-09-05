"""Alerts router — GET /api/v1/alerts"""
from typing import List
from fastapi import APIRouter
from app.services.alerts.engine import alert_engine
from app.providers import synthetic_rainfall, synthetic_drainage
from app.schemas import Alert

router = APIRouter()

@router.get("/alerts", response_model=List[Alert])
async def get_alerts():
    """Current active alerts. Decision-support only — not official orders."""
    intensity = synthetic_rainfall.current_intensity
    drainage = await synthetic_drainage.get_network_status(intensity)
    return alert_engine.generate(intensity, drainage)
