# FLOOD-X Backend Dockerfile
# Uses Python 3.11 for stable geospatial package support
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ML_MODELS_DIR=/app/models \
    APP_ENV=production

# Install system dependencies for geospatial packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ ./app/
COPY run.py .

# Copy pre-trained ML models (built from scripts/train_models.py)
RUN mkdir -p /app/models
COPY models/ /app/models/

# Create non-root user
RUN useradd -m -u 1000 floodx && chown -R floodx:floodx /app
USER floodx

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
