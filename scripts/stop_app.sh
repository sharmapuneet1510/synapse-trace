#!/usr/bin/env bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT/backend/logs/app.pid"
if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  kill "$PID" 2>/dev/null && echo "[stop_app] Stopped pid=$PID" || echo "[stop_app] Process not found"
  rm -f "$PID_FILE"
else
  echo "[stop_app] No PID file found"
fi
