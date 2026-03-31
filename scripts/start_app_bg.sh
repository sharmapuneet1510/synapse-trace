#!/usr/bin/env bash
# ── Start the FastAPI app in the background (nohup) ──────────────────────────
# Usage:  ./scripts/start_app_bg.sh
# PID is written to backend/logs/app.pid

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p backend/logs
PID_FILE="backend/logs/app.pid"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "[start_app_bg] Already running (pid=$(cat $PID_FILE)). Stop it first."
  exit 1
fi

nohup bash scripts/start_app.sh >> backend/logs/app.log 2>&1 &
echo $! > "$PID_FILE"
echo "[start_app_bg] Started (pid=$!). Logs → backend/logs/app.log"
