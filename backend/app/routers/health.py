"""Health check router — GET /api/v1/health"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    """Returns API health status, version, and current timestamp."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_mode": "SYNTHETIC_SIMULATION",
        "pilot_city": settings.PILOT_CITY,
    }
