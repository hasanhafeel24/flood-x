"""
FLOOD-X Demo Mode — Deterministic Scenario Orchestrator
=========================================================
Provides a single-click, fully reproducible demo for SIH evaluation.

The demo runs a fixed 8-phase sequence simulating the 2015-style
Chennai extreme rainfall event. Seed=42 ensures identical output
on every run for judge consistency.

Endpoint: POST /api/v1/demo/start
         GET  /api/v1/demo/status
         POST /api/v1/demo/reset

DATA SOURCE: SYNTHETIC_PROTOTYPE — deterministic seed=42
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

import structlog

log = structlog.get_logger(__name__)


@dataclass
class DemoPhase:
    """A single phase in the demo narrative."""
    name: str
    description: str
    scenario: str
    intensity_target: float          # mm/hr to ramp to
    duration_steps: int              # simulation ticks at 5s each
    key_observation: str             # what the judge should observe
    expected_risk: str               # LOW/MODERATE/HIGH/CRITICAL


# ── 8-Phase Chennai Extreme Rainfall Scenario ──────────────────────────────────
# Modelled on the November 2015 Chennai floods (1049mm in 24 hours)
# DATA: SYNTHETIC_PROTOTYPE — approximate intensities, not observed data

DEMO_PHASES: List[DemoPhase] = [
    DemoPhase(
        name="Phase 1 — System Normal",
        description="System monitoring active. Light morning drizzle. All drainage within capacity.",
        scenario="normal_rainfall",
        intensity_target=4.0,
        duration_steps=6,
        key_observation="All zones GREEN. Drainage utilization < 30%. No alerts.",
        expected_risk="LOW",
    ),
    DemoPhase(
        name="Phase 2 — Rainfall Beginning",
        description="Southwest monsoon onset. Rainfall intensifying over Velachery catchment.",
        scenario="normal_rainfall",
        intensity_target=18.0,
        duration_steps=6,
        key_observation="Nowcast T+60min showing MODERATE risk in Velachery. Drainage loading.",
        expected_risk="LOW",
    ),
    DemoPhase(
        name="Phase 3 — Heavy Rainfall",
        description="IMD HEAVY threshold crossed (35.5 mm/hr). Drainage load rising rapidly.",
        scenario="heavy_rainfall",
        intensity_target=52.0,
        duration_steps=8,
        key_observation="WATCH alert issued. 4+ drainage nodes approaching capacity. Public advisory triggered.",
        expected_risk="MODERATE",
    ),
    DemoPhase(
        name="Phase 4 — Critical Drainage Load",
        description="Drainage network reaching saturation. Multiple surcharging nodes detected.",
        scenario="heavy_rainfall",
        intensity_target=78.0,
        duration_steps=8,
        key_observation="WARNING alert. 8+ nodes surcharging. Flood Clock showing T-25min for Velachery.",
        expected_risk="HIGH",
    ),
    DemoPhase(
        name="Phase 5 — Extreme Rainfall (Peak)",
        description="EXTREME rainfall event (>115 mm/hr). Surface flooding initiated. Drainage overwhelmed.",
        scenario="extreme_rainfall",
        intensity_target=132.0,
        duration_steps=10,
        key_observation="EMERGENCY alert. Velachery CRITICAL (depth 45cm). Safe Route rerouted via ORR bypass.",
        expected_risk="CRITICAL",
    ),
    DemoPhase(
        name="Phase 6 — Decision Support Active",
        description="AI decision engine issuing ranked recommendations to EOC.",
        scenario="extreme_rainfall",
        intensity_target=118.0,
        duration_steps=8,
        key_observation="6 recommendations: pump deploy, road closure, NDRF pre-position, evacuation advisory.",
        expected_risk="CRITICAL",
    ),
    DemoPhase(
        name="Phase 7 — Rainfall Subsiding",
        description="Rainfall intensity declining. Drainage recovery beginning.",
        scenario="normal_rainfall",
        intensity_target=30.0,
        duration_steps=8,
        key_observation="Risk downgrading HIGH → MODERATE. Safe routes partially reopening.",
        expected_risk="HIGH",
    ),
    DemoPhase(
        name="Phase 8 — Recovery Phase",
        description="Rainfall ended. Drainage recovering. System returning to normal monitoring.",
        scenario="normal_rainfall",
        intensity_target=5.0,
        duration_steps=6,
        key_observation="All zones returning to LOW/MODERATE. No active alerts. Monitoring continues.",
        expected_risk="LOW",
    ),
]


@dataclass
class DemoStatus:
    is_running: bool = False
    current_phase_idx: int = 0
    current_phase_name: str = "Not started"
    key_observation: str = ""
    expected_risk: str = "LOW"
    total_phases: int = len(DEMO_PHASES)
    elapsed_seconds: float = 0.0
    data_source: str = "SYNTHETIC_PROTOTYPE"
    note: str = "Deterministic demo — seed=42. Results identical on every run."


class DemoOrchestrator:
    """
    Manages the deterministic SIH demo scenario.

    Coordinates with SimulationEngine to step through phases
    automatically, providing a compelling judge presentation.
    """

    def __init__(self) -> None:
        self._status = DemoStatus()
        self._task: Optional[asyncio.Task] = None
        self._start_time: float = 0.0

    async def start(self) -> DemoStatus:
        """Start the demo from phase 1."""
        if self._status.is_running:
            await self.reset()

        from app.simulation.engine import SimulationEngine
        engine = SimulationEngine.get_instance()

        self._status.is_running = True
        self._status.current_phase_idx = 0
        self._start_time = asyncio.get_event_loop().time()

        log.info("demo_started", phases=len(DEMO_PHASES))
        self._task = asyncio.create_task(self._run_phases(engine))
        return self._status

    async def _run_phases(self, engine) -> None:
        """Step through all demo phases automatically."""
        import time

        for i, phase in enumerate(DEMO_PHASES):
            self._status.current_phase_idx = i
            self._status.current_phase_name = phase.name
            self._status.key_observation = phase.key_observation
            self._status.expected_risk = phase.expected_risk

            log.info("demo_phase", phase=phase.name, target_intensity=phase.intensity_target)

            # Start the simulation scenario for this phase
            await engine.start(scenario=phase.scenario, speed=2.0)

            # Ramp intensity to target
            await engine.set_rainfall_intensity(phase.intensity_target)

            # Run for the phase duration (each step is 5s at 2x speed = 2.5s wall time)
            await asyncio.sleep(phase.duration_steps * 2.5)

            if not self._status.is_running:
                break

        self._status.is_running = False
        self._status.current_phase_name = "Demo Complete"
        self._status.key_observation = "Full pipeline demonstrated. All 8 phases complete."
        log.info("demo_complete")

    async def reset(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._status = DemoStatus()
        log.info("demo_reset")

    @property
    def status(self) -> DemoStatus:
        import time
        self._status.elapsed_seconds = (
            asyncio.get_event_loop().time() - self._start_time
            if self._status.is_running else 0.0
        )
        return self._status


# Singleton
demo_orchestrator = DemoOrchestrator()
