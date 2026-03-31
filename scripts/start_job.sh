#!/usr/bin/env bash
# Run the data lineage scanning job (foreground)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f "backend/.venv/bin/activate" ]; then
  source backend/.venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "[job] Starting data lineage scan..."
python -m backend.job.data_lineage "$@"
echo "[job] Done."
