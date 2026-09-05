"""
FLOOD-X Simulation Engine — Scenario-based Event Loop
======================================================
Drives the real-time simulation:
  - Advances simulation time
  - Updates rainfall provider
  - Runs hydrology → drainage → nowcast pipeline
  - Broadcasts state via WebSocket
  - Deterministic demo mode (seed=42)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog

from app.providers import synthetic_rainfall, synthetic_drainage
from app.providers import SCENARIOS
from app.schemas import SimulationScenario, SimulationState
from app.services.nowcast.engine import nowcast_engine

log = structlog.get_logger(__name__)

# Phase labels for demo narrative
PHASE_LABELS = [
    "System Normal — Monitoring",
    "Rainfall Beginning",
    "Rainfall Intensifying",
    "Drainage Load Rising",
    "Approaching Capacity",
    "Critical Bottleneck Detected",
    "Flooding Predicted",
    "Flood Clock Active",
    "Road Risk Elevated",
    "Safe Routes Recalculated",
    "Emergency Recommendations Issued",
    "Rainfall Subsiding",
    "Recovery Phase",
]


class SimulationEngine:
    """Singleton simulation engine — drives the FLOOD-X real-time loop."""

    _instance: Optional[SimulationEngine] = None

    def __init__(self) -> None:
        self._run_id: str = str(uuid.uuid4())
        self._scenario: str = "normal_rainfall"
        self._is_running: bool = False
        self._is_paused: bool = False
        self._speed: float = 1.0
        self._step: int = 0
        self._total_steps: int = 120  # 10 minutes of sim at 5s ticks
        self._start_wall_time: float = time.time()
        self._task: Optional[asyncio.Task] = None
        self._last_state: Optional[SimulationState] = None

    @classmethod
    def get_instance(cls) -> SimulationEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self, scenario: str = "normal_rainfall", speed: float = 1.0) -> None:
        if self._is_running:
            await self.reset()

        self._scenario = scenario
        self._speed = speed
        self._run_id = str(uuid.uuid4())
        self._step = 0
        self._is_running = True
        self._is_paused = False
        self._start_wall_time = time.time()

        # Reset hydrology state
        from app.services.hydrology.engine import hydrology_engine
        hydrology_engine.reset_antecedent_moisture()

        log.info("simulation_started", run_id=self._run_id, scenario=scenario)
        self._task = asyncio.create_task(self._loop())

    async def pause(self) -> None:
        self._is_paused = True
        log.info("simulation_paused")

    async def resume(self) -> None:
        self._is_paused = False
        log.info("simulation_resumed")

    async def reset(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._is_running = False
        self._is_paused = False
        self._step = 0
        self._scenario = "normal_rainfall"
        log.info("simulation_reset")

        # Broadcast reset
        from app.websocket.manager import ws_manager
        await ws_manager.broadcast({
            "type": "simulation_reset",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def set_rainfall_intensity(self, intensity: float) -> None:
        synthetic_rainfall._base_intensity = max(0.0, intensity)
        log.info("rainfall_intensity_set", intensity=intensity)

    async def _loop(self) -> None:
        """Main simulation tick loop."""
        from app.websocket.manager import ws_manager
        from app.services.nowcast.engine import nowcast_engine

        tick_interval = 5.0 / self._speed  # seconds between ticks

        while self._is_running and self._step <= self._total_steps:
            if self._is_paused:
                await asyncio.sleep(0.5)
                continue

            step_fraction = self._step / max(self._total_steps, 1)

            # Update rainfall based on scenario progress
            synthetic_rainfall.set_scenario(self._scenario, step_fraction)
            intensity = synthetic_rainfall.current_intensity
            accumulated = synthetic_rainfall._accumulated

            # Update nowcast engine
            nowcast_engine.update_state(intensity, accumulated, self._scenario)

            # Phase label
            phase_idx = min(
                int(step_fraction * len(PHASE_LABELS)),
                len(PHASE_LABELS) - 1
            )
            phase_label = PHASE_LABELS[phase_idx]

            # Build state
            state = SimulationState(
                run_id=self._run_id,
                scenario=SimulationScenario(self._scenario),
                is_running=True,
                is_paused=False,
                elapsed_seconds=time.time() - self._start_wall_time,
                simulated_time=datetime.now(timezone.utc),
                rainfall_intensity_mm_hr=round(intensity, 2),
                step=self._step,
                total_steps=self._total_steps,
                phase_label=phase_label,
            )
            self._last_state = state

            # Get current drainage status
            drainage = await synthetic_drainage.get_network_status(
                intensity,
                SCENARIOS.get(self._scenario, {}).get("drainage_modifier", 1.0),
            )

            # Get current rainfall
            rainfall_obs = await synthetic_rainfall.get_current()

            # Generate alerts
            from app.services.alerts.engine import alert_engine
            alerts = alert_engine.generate(intensity, drainage, self._step)

            # Broadcast to all WebSocket clients
            await ws_manager.broadcast({
                "type": "simulation_tick",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_mode": "SYNTHETIC_SIMULATION",
                "simulation": state.model_dump(),
                "rainfall": {
                    "intensity_mm_hr": round(intensity, 2),
                    "accumulated_mm": round(accumulated, 2),
                    "source": "SYNTHETIC_PROTOTYPE",
                },
                "drainage": {
                    "overall_status": drainage.overall_status,
                    "average_utilization_pct": drainage.average_utilization_pct,
                    "surcharging_nodes": drainage.surcharging_nodes,
                    "bottleneck_nodes": drainage.bottleneck_nodes,
                },
                "alerts": [a.model_dump() for a in alerts[:5]],
                "phase": phase_label,
            })

            self._step += 1
            await asyncio.sleep(tick_interval)

        # Simulation complete
        self._is_running = False
        await ws_manager.broadcast({
            "type": "simulation_complete",
            "run_id": self._run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        log.info("simulation_complete", run_id=self._run_id)

    @property
    def current_state(self) -> Optional[SimulationState]:
        return self._last_state

    @property
    def is_running(self) -> bool:
        return self._is_running
