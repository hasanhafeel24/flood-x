# FLOOD-X Backend Dockerfile
# ===========================
# Uses Python 3.11 for stable geospatial package support.
# Installs production dependencies only (no GDAL, no dev tools).
# Application runs in SYNTHETIC data mode (no external data source APIs needed).

FROM python:3.11-slim-bookworm

# Environment hardening
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Models dir resolves to /app/models in container
    ML_MODELS_DIR=/app/models \
    APP_ENV=production \
    APP_DEBUG=false \
    BACKEND_RELOAD=false

# Install minimal system dependencies
# psycopg2-binary bundles its own libpq — no libpq-dev needed in slim image
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (production only — no GDAL, no dev tools)
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy source code
COPY app/ ./app/
COPY run.py .

# Copy pre-trained ML models
# models/ directory contains: xgboost_classifier_v1.json,
# xgboost_regressor_v1.json, scaler_v1.pkl, training_metadata_v1.json
RUN mkdir -p /app/models
COPY models/ /app/models/

# Create non-root user for security
RUN useradd -m -u 1000 floodx && chown -R floodx:floodx /app
USER floodx

EXPOSE 8000

# Production: PORT is injected by container orchestrator.
# Falls back to 8000 if not set.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info"]
