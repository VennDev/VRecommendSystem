# Build stage - install dependencies
FROM python:3.9.23-slim AS builder

WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry
RUN pip install --no-cache-dir poetry

# Configure Poetry: Don't create virtual environment
RUN poetry config virtualenvs.create false

# Copy ONLY Poetry configuration files first (for dependency caching)
COPY pyproject.toml poetry.lock* ./

# Regenerate lock file if needed, then install dependencies
# This layer will be cached unless pyproject.toml changes
RUN poetry lock && \
    poetry install --only=main --no-interaction --no-ansi --no-root

# Production stage
FROM python:3.9.23-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create the same directory structure as development
# Hydra config_path="../../../config" expects:
# /app/src/ai_server/config/config.py -> ../../../config = /app/config
RUN mkdir -p /app/src

# Copy source code maintaining structure for Hydra relative paths
COPY --chown=appuser:appgroup src/ai_server ./src/ai_server

# Copy config to /app/config (matches ../../../config from src/ai_server/config/)
COPY --chown=appuser:appgroup config/ ./config/

# Copy models
COPY --chown=appuser:appgroup models/ ./models/

# Copy tasks
COPY --chown=appuser:appgroup tasks/ ./tasks/

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app/logs

# Set Python environment
# PYTHONPATH includes /app/src so 'import ai_server' works
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 9999

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9999/api/v1/health || exit 1

# Command to run the application
CMD ["python", "-m", "ai_server.main"]
