"""
Alembic Environment — FLOOD-X
================================
Supports both offline (SQL script) and online (live DB) migration modes.
Uses async engine for online migrations (asyncpg).

Reads DATABASE_SYNC_URL from environment (psycopg2 for Alembic compatibility).
"""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Add backend to path so app imports work ───────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# ── Import app metadata ───────────────────────────────────────────────────────
from app.core.database import Base  # noqa: E402 — must be after sys.path
import app.models  # noqa: F401 — ensure all models are registered

# Alembic Config object
config = context.config

# Override sqlalchemy.url from environment if set
db_url = os.getenv("DATABASE_SYNC_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Offline mode: emit SQL to stdout without a live DB connection.
    Useful for generating migration scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online mode: connect to DB and apply migrations directly.
    Uses synchronous psycopg2 driver (Alembic requirement).
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
