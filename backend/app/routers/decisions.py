"""Decisions router — GET /api/v1/decisions/current"""
from fastapi import APIRouter
from app.services.decisions.engine import decision_engine, DecisionPackage, Recommendation
from app.services.nowcast.engine import nowcast_engine
from app.providers import synthetic_drainage, synthetic_rainfall
from app.schemas import RiskLevel
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class RecommendationOut(BaseModel):
    rec_id: str
    category: str
    urgency: str
    priority_rank: int
    title: str
    rationale: str
    action_steps: List[str]
    target_locations: List[str]
    estimated_impact: str
    estimated_resources: str
    deadline_minutes: Optional[int]
    confidence: float
    triggered_by: str
    issued_at: datetime
    data_source: str
    disclaimer: str

    @classmethod
    def from_rec(cls, r: Recommendation) -> "RecommendationOut":
        return cls(
            rec_id=r.rec_id,
            category=r.category.value,
            urgency=r.urgency.value,
            priority_rank=r.priority_rank,
            title=r.title,
            rationale=r.rationale,
            action_steps=r.action_steps,
            target_locations=r.target_locations,
            estimated_impact=r.estimated_impact,
            estimated_resources=r.estimated_resources,
            deadline_minutes=r.deadline_minutes,
            confidence=r.confidence,
            triggered_by=r.triggered_by,
            issued_at=r.issued_at,
            data_source=r.data_source,
            disclaimer=r.disclaimer,
        )


@router.get("/decisions/current")
async def get_current_decisions():
    """
    Generate current decision support package.

    Returns prioritised recommendations for the current hydraulic state.
    ALL recommendations are DECISION-SUPPORT ONLY — not official orders.
    DATA SOURCE: SYNTHETIC_PROTOTYPE
    """
    intensity = synthetic_rainfall.current_intensity
    drainage = await synthetic_drainage.get_network_status(intensity)
    nowcasts = await nowcast_engine.generate_nowcasts()

    flooded_zones = sum(
        1 for nc in nowcasts
        if nc.current_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    )
    max_depth = max((nc.current_depth_cm for nc in nowcasts), default=0.0)
    accumulated = getattr(synthetic_rainfall, "_accumulated", 0.0)

    package = decision_engine.generate(
        intensity_mm_hr=intensity,
        accumulated_mm=accumulated,
        drainage=drainage,
        flooded_zones=flooded_zones,
        total_zones=len(nowcasts),
        max_depth_cm=max_depth,
        overall_risk=drainage.overall_status,
    )

    return {
        "package_id": package.package_id,
        "issued_at": package.issued_at.isoformat(),
        "overall_risk": package.overall_risk.value,
        "situation_summary": package.situation_summary,
        "total_recommendations": package.total_recommendations,
        "immediate_actions": package.immediate_actions,
        "recommendations": [RecommendationOut.from_rec(r) for r in package.recommendations],
        "data_source": "SYNTHETIC_PROTOTYPE",
        "disclaimer": package.disclaimer,
    }
