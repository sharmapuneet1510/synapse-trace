#!/usr/bin/env bash
# Start the frontend dev server (foreground)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

MODE="${1:-dev}"  # dev | preview

if [ "$MODE" = "preview" ]; then
  echo "[frontend] Building and starting preview server..."
  npm run build
  npm run preview
else
  echo "[frontend] Starting dev server..."
  npm run dev
fi
