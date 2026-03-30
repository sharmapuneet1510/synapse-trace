#!/usr/bin/env python3
"""Start the Data Lineage Platform backend API server."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import uvicorn
from modules.backend_api.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
