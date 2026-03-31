#!/usr/bin/env bash
# Stop the background data lineage job
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/backend/logs/job.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "[job] No PID file found. Job may not be running."
  exit 0
fi

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "[job] Stopped (PID $PID)."
else
  echo "[job] Process $PID not running."
fi
rm -f "$PID_FILE"
