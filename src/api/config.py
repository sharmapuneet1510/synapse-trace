from __future__ import annotations

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
JURISDICTION_JSON = BASE_DIR / "jurisdiction.json"

# API
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
