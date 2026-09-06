"""FLOOD-X Core Configuration — Pydantic Settings."""

from functools import lru_cache
from typing import List

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
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # ── Server ─────────────────────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_RELOAD: bool = True

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://floodx:floodx_dev_password@localhost:5432/floodx"
    )
    DATABASE_SYNC_URL: str = (
        "postgresql+psycopg2://floodx:floodx_dev_password@localhost:5432/floodx"
    )

    # ── Security ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── CORS ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:5174"
    # Regex to allow any Railway/Vercel/Render preview URL automatically
    CORS_ORIGINS_REGEX: str = r"https://.*\.(vercel\.app|railway\.app|onrender\.com|up\.railway\.app)"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # ── Data Providers ─────────────────────────────────────────────────────────
    RAINFALL_PROVIDER: str = "synthetic"
    TERRAIN_PROVIDER: str = "synthetic"
    DRAINAGE_PROVIDER: str = "synthetic"

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
    # Resolves to /app/models in Docker, or ../models in local dev
    ML_MODELS_DIR: str = "../models"
    ML_PRIMARY_MODEL: str = "xgboost_v1"
    ML_CONFIDENCE_THRESHOLD: float = 0.5


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
