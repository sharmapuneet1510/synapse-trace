#!/usr/bin/env bash
# ── Start the FastAPI app (backend/app) ───────────────────────────────────────
# Usage:  ./scripts/start_app.sh [--port 8000] [--workers 1]
# Runs uvicorn in the foreground; use nohup for background:
#   nohup ./scripts/start_app.sh >> backend/logs/app.log 2>&1 &

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
ENV="${APP_ENV:-development}"

mkdir -p backend/logs

export LOG_DIR="$ROOT/backend/logs"
export PYTHONPATH="$ROOT/backend/job:$ROOT"

echo "[start_app] root=$ROOT  port=$PORT  env=$ENV"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

if [ "$ENV" = "production" ]; then
  exec uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "$WORKERS" \
    --no-access-log
else
  exec uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --reload \
    --reload-dir backend/app
fi
