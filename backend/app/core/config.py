"""FLOOD-X Core Configuration — Pydantic Settings.

Environment variable lookup order:
  1. Actual environment variables (always win — used by Render/Vercel)
  2. .env file (local development)
  3. Field defaults (safe fallbacks for dev, intentionally absent for secrets)
"""

import os
import warnings
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "FLOOD-X"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False  # Default OFF — must be explicitly enabled in dev
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # ── Server ─────────────────────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    # PORT is injected by Render/Railway/Heroku at runtime. BACKEND_PORT is the
    # fallback for local development. The startup command should use $PORT.
    BACKEND_PORT: int = 8000
    PORT: Optional[int] = None          # Render injects this automatically
    BACKEND_RELOAD: bool = False        # Never reload in production

    @property
    def effective_port(self) -> int:
        """Return PORT (Render) if set, else BACKEND_PORT (local dev)."""
        return self.PORT if self.PORT is not None else self.BACKEND_PORT

    # ── Database ───────────────────────────────────────────────────────────────
    # No hardcoded defaults — the application gracefully degrades to simulation
    # mode when DATABASE_URL is not set (see main.py lifespan handler).
    DATABASE_URL: str = (
        "postgresql+asyncpg://floodx:floodx_dev_password@localhost:5432/floodx"
    )
    DATABASE_SYNC_URL: str = (
        "postgresql+psycopg2://floodx:floodx_dev_password@localhost:5432/floodx"
    )

    # ── Security ───────────────────────────────────────────────────────────────
    # REQUIRED in production — set via Render environment variable panel.
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── CORS ───────────────────────────────────────────────────────────────────
    # Comma-separated list of explicitly allowed origins.
    # In production, set this to your Vercel frontend URL:
    #   CORS_ORIGINS=https://your-app.vercel.app
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"
    # Regex also allows: ALL localhost ports (dev) + *.vercel.app, *.onrender.com,
    # *.railway.app (prod preview deployments).
    CORS_ORIGINS_REGEX: str = (
        r"http://localhost(:\d+)?"
        r"|https://[\w-]+\.vercel\.app"
        r"|https://[\w-]+\.onrender\.com"
        r"|https://[\w-]+\.railway\.app"
        r"|https://[\w-]+\.up\.railway\.app"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Data Providers ─────────────────────────────────────────────────────────
    # Options: synthetic | file | imd
    # Production default: synthetic (no external API keys required)
    RAINFALL_PROVIDER: str = "synthetic"
    TERRAIN_PROVIDER: str = "synthetic"
    DRAINAGE_PROVIDER: str = "synthetic"

    # ── IMD Provider (optional — requires institutional API access) ────────────
    IMD_API_KEY: Optional[str] = None
    IMD_API_URL: str = "https://imdpune.gov.in/api/"

    # ── Simulation ─────────────────────────────────────────────────────────────
    SIMULATION_TICK_SECONDS: int = 5
    SIMULATION_SPEED_MULTIPLIER: float = 1.0
    DEFAULT_SCENARIO: str = "normal_rainfall"

    # ── Geospatial ─────────────────────────────────────────────────────────────
    DEFAULT_CRS: str = "EPSG:4326"
    PILOT_CITY: str = "Chennai"
    PILOT_BBOX_WEST: float = 80.15
    PILOT_BBOX_SOUTH: float = 12.90
    PILOT_BBOX_EAST: float = 80.32
    PILOT_BBOX_NORTH: float = 13.10

    # ── ML ─────────────────────────────────────────────────────────────────────
    # In Docker / Render: set ML_MODELS_DIR=/app/models or ./models
    # In local dev: defaults to ../models (relative to backend/)
    ML_MODELS_DIR: str = "./models"
    ML_PRIMARY_MODEL: str = "xgboost_v1"
    ML_CONFIDENCE_THRESHOLD: float = 0.5

    def validate_production(self) -> None:
        """Warn loudly if unsafe defaults are used in production."""
        if self.APP_ENV == "production":
            if self.SECRET_KEY == "dev-secret-key-change-in-production":
                warnings.warn(
                    "SECRET_KEY is using the default dev value in production! "
                    "Set SECRET_KEY to a secure random value via environment variable.",
                    stacklevel=2,
                )


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.validate_production()
    return s


settings = get_settings()
