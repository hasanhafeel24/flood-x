"""FLOOD-X Database Engine and Session Management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all FLOOD-X ORM models."""
    pass


# ── Import all models so Base.metadata knows about every table ────────────────
# This ensures create_all() and Alembic autogenerate both work correctly.
# noqa: F401 — imports are side-effect-only (register with metadata)
def _import_models() -> None:
    from app.models.flood_event import FloodEvent       # noqa: F401
    from app.models.alert_log import AlertLog            # noqa: F401
    from app.models.simulation_run import SimulationRun  # noqa: F401

_import_models()


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
