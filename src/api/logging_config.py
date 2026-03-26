"""Centralized logging configuration for Synapse Trace API.

Call setup_logging() once at application startup. All modules then use
logging.getLogger(__name__) and inherit this configuration automatically.

Log level can be overridden via the LOG_LEVEL environment variable:
    LOG_LEVEL=DEBUG uvicorn src.api.main:app --reload
"""
from __future__ import annotations

import logging
import os
import sys


def setup_logging() -> None:
    """Configure root logger with consistent format and level."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=date_fmt,
        stream=sys.stdout,
        force=True,
    )

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised — level=%s", level_name
    )
