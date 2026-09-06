"""
FLOOD-X Backend — FastAPI Application Factory
==============================================
AI-Powered Urban Flood Nowcasting & Decision Support System
SIH 2026 — Problem Statement SIH26085
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.database import engine, Base
from app.routers import (
    health,
    rainfall,
    flood,
    drainage,
    routes as routing,
    alerts,
    simulation,
    system,
    decisions,
    demo,
    explain,
)
from app.websocket.manager import ws_manager

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup → serve → shutdown."""
    configure_logging()
    log.info("flood_x_startup", version=settings.APP_VERSION, env=settings.APP_ENV)

    # Create database tables if they don't exist
    # In production with Alembic: alembic upgrade head
    # Graceful fallback: backend works in SIMULATION mode without PostgreSQL
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("database_tables_initialized")
    except Exception as db_err:
        log.warning(
            "database_unavailable_simulation_mode",
            error=str(db_err),
            mode="SYNTHETIC_SIMULATION — no persistence",
        )

    log.info("flood_x_ready", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT)
    yield

    # Shutdown
    log.info("flood_x_shutdown")
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="FLOOD-X API",
        description=(
            "AI-Powered Urban Flood Nowcasting & Decision Support System. "
            "SIH 2026 — SIH26085. "
            "All simulation data is clearly labelled as SYNTHETIC/SIMULATED."
        ),
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.CORS_ORIGINS_REGEX,  # covers *.vercel.app, *.railway.app
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Routers ─────────────────────────────────────────────────────────────────
    prefix = "/api/v1"
    app.include_router(health.router,     prefix=prefix, tags=["health"])
    app.include_router(rainfall.router,   prefix=prefix, tags=["rainfall"])
    app.include_router(flood.router,      prefix=prefix, tags=["flood"])
    app.include_router(drainage.router,   prefix=prefix, tags=["drainage"])
    app.include_router(routing.router,    prefix=prefix, tags=["routing"])
    app.include_router(alerts.router,     prefix=prefix, tags=["alerts"])
    app.include_router(simulation.router, prefix=prefix, tags=["simulation"])
    app.include_router(system.router,     prefix=prefix, tags=["system"])
    app.include_router(decisions.router,  prefix=prefix, tags=["decisions"])
    app.include_router(demo.router,       prefix=prefix, tags=["demo"])
    app.include_router(explain.router,    prefix=prefix, tags=["explain"])  # XGBoost explainability

    # ── WebSocket ───────────────────────────────────────────────────────────────
    @app.websocket("/ws")
    async def websocket_endpoint(websocket):
        await ws_manager.handle_connection(websocket)

    return app


app = create_app()
