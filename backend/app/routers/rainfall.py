"""Rainfall router — GET /api/v1/rainfall/*"""
from fastapi import APIRouter
from app.providers import synthetic_rainfall, synthetic_drainage
from app.schemas import RainfallObservation
from typing import List

router = APIRouter()

@router.get("/rainfall/current", response_model=RainfallObservation)
async def get_current_rainfall():
    """Current rainfall observation. DATA SOURCE: SYNTHETIC_PROTOTYPE"""
    return await synthetic_rainfall.get_current()

@router.get("/rainfall/forecast", response_model=List[RainfallObservation])
async def get_rainfall_forecast(hours: int = 3):
    """0–3 hour rainfall forecast at 15-min intervals. DATA: SYNTHETIC_PROTOTYPE"""
    hours = min(max(hours, 1), 3)
    return await synthetic_rainfall.get_forecast(hours)
