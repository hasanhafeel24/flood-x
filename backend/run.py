"""FLOOD-X Backend — Entry Point for Uvicorn.

Production start command (Render):
    uvicorn app.main:app --host 0.0.0.0 --port $PORT

Development:
    python run.py   (uses BACKEND_PORT from .env, default 8000)
"""

import uvicorn
from app.core.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.effective_port,
        reload=settings.BACKEND_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
