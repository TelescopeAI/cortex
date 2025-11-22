# Use ARM64-native image on Apple Silicon (automatic selection)
# Docker will automatically use arm64 variant if available
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Use psycopg2-binary for faster install (no compilation needed)
RUN pip install --no-cache-dir psycopg2-binary gunicorn poetry

WORKDIR /app

# Copy dependency files first (for better layer caching)
COPY pyproject.toml poetry.lock __version__.py ./

# Install dependencies (this layer will be cached if dependencies don't change)
RUN poetry config virtualenvs.create false && \
    poetry install --with api --no-interaction --no-ansi --no-root

# Copy application code (this changes more frequently)
COPY cortex/ ./cortex/

# Copy migrations directory (needed for auto-migration on startup)
COPY migrations/ ./migrations/

EXPOSE 9002

# Configure healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:9002/ || exit 1

# Run API Server with proper logging enabled
ENTRYPOINT ["gunicorn", "-w", "4", \
            "-k", "uvicorn.workers.UvicornWorker", \
            "-b", "0.0.0.0:9002", \
            "--keep-alive", "360", \
            "--timeout", "360", \
            "--access-logfile", "-", \
            "--error-logfile", "-", \
            "--access-logformat", "'%(h)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"'", \
            "--log-level", "debug", \
            "--logger-class", "gunicorn.glogging.Logger", \
            "cortex.api.main:app"]

