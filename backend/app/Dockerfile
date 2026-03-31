# ── Stage 1: build deps ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build toolchain (needed for lxml, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/requirements.txt ./

RUN pip install --upgrade pip \
 && pip install --no-cache-dir \
        fastapi \
        "uvicorn[standard]" \
        "pydantic>=2.0" \
        sqlalchemy \
        networkx \
        pyvis \
        lxml \
        jinja2 \
        anthropic \
 && pip install --no-cache-dir -r requirements.txt || true


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="synapse-trace-api" \
      org.opencontainers.image.description="Synapse Trace — FastAPI backend" \
      org.opencontainers.image.source="$CI_PROJECT_URL"

RUN apt-get update && apt-get install -y --no-install-recommends \
        libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY backend/app/       ./backend/app/
COPY backend/job/       ./backend/job/
COPY backend/config/    ./backend/config/

# trace_core lives inside backend/job/ — add it to PYTHONPATH so the app
# can resolve `from trace_core.*` imports without installing it as a package.
ENV PYTHONPATH="/app/backend/job:/app" \
    LOG_DIR="/app/backend/logs" \
    APP_ENV="production" \
    PORT="8000"

RUN mkdir -p /app/backend/logs /app/backend/output/html /app/backend/output/json /app/backend/output/md

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["sh", "-c", \
     "uvicorn backend.app.main:app \
        --host 0.0.0.0 \
        --port ${PORT} \
        --workers ${WORKERS:-2} \
        --no-access-log"]
