# ── Stage 1: build deps ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/requirements.txt ./

RUN pip install --upgrade pip \
 && pip install --no-cache-dir \
        networkx \
        pyvis \
        lxml \
        jinja2 \
 && pip install --no-cache-dir -r requirements.txt || true


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="synapse-trace-job" \
      org.opencontainers.image.description="Synapse Trace — data lineage scanning job" \
      org.opencontainers.image.source="$CI_PROJECT_URL"

RUN apt-get update && apt-get install -y --no-install-recommends \
        libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Only the job subtree is needed; trace_core is co-located under backend/job/
COPY backend/job/       ./backend/job/
COPY backend/config/    ./backend/config/

ENV PYTHONPATH="/app/backend/job:/app" \
    LOG_DIR="/app/backend/logs"

RUN mkdir -p /app/backend/logs \
             /app/backend/output/html \
             /app/backend/output/json \
             /app/backend/output/md

# Mount source repos at /repos at runtime:
#   docker run -v /path/to/repos:/repos synapse-trace-job \
#              --project-repos /repos/trade-service
VOLUME ["/repos", "/app/backend/output"]

CMD ["python", "-m", "backend.job.data_lineage"]
