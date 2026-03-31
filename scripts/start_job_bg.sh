#!/usr/bin/env bash
# Run the data lineage scanning job in the background (nohup)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/backend/logs/job.pid"
LOG_FILE="$ROOT/backend/logs/job.log"

mkdir -p "$ROOT/backend/logs"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "[job] Already running (PID $PID). Use stop_job.sh to stop it."
    exit 1
  fi
  rm -f "$PID_FILE"
fi

echo "[job] Starting data lineage scan in background..."
nohup bash "$ROOT/scripts/start_job.sh" "$@" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "[job] Started (PID $(cat "$PID_FILE")). Logs: $LOG_FILE"
