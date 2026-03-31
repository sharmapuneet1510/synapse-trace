"""Centralized structured logging for Synapse Trace API.

Features:
- JSON-formatted log records (one line per entry) for production log aggregators
- Human-readable colored format for local development
- Rotating file handlers:  logs/app.log  (all levels)  +  logs/error.log (ERROR+)
- Log level controlled by LOG_LEVEL env var (default INFO)
- Audit logger at logs/audit.log for security-relevant events

Call setup_logging() once at application startup.
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import time
from pathlib import Path


# ── JSON formatter ────────────────────────────────────────────────────────────

class _JsonFormatter(logging.Formatter):
    """Emit one compact JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts":      self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":   record.levelname,
            "logger":  record.name,
            "msg":     record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Carry through any extra fields attached via logger.info(msg, extra={...})
        for key in ("trace_id", "field_name", "user_id", "session_id",
                    "request_id", "jurisdiction_id", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, default=str)


# ── Console formatter (dev) ───────────────────────────────────────────────────

class _DevFormatter(logging.Formatter):
    LEVEL_COLORS = {
        "DEBUG":    "\033[36m",
        "INFO":     "\033[32m",
        "WARNING":  "\033[33m",
        "ERROR":    "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelname, "")
        ts = self.formatTime(record, "%H:%M:%S")
        base = f"{ts} {color}{record.levelname:<8}{self.RESET} {record.name} | {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_logging() -> None:
    """Configure root and module loggers.

    Environment variables
    ---------------------
    LOG_LEVEL   : DEBUG / INFO / WARNING / ERROR  (default: INFO)
    LOG_FORMAT  : json / dev                      (default: dev for local, json if LOG_FORMAT set)
    LOG_DIR     : directory for rotating log files (default: logs/)
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level      = getattr(logging, level_name, logging.INFO)
    fmt_mode   = os.environ.get("LOG_FORMAT", "dev").lower()
    log_dir    = Path(os.environ.get("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)
    # Clear any handlers already attached (e.g. from basicConfig)
    root.handlers.clear()

    # ── Console handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    if fmt_mode == "json":
        console_handler.setFormatter(_JsonFormatter())
    else:
        console_handler.setFormatter(_DevFormatter())
    root.addHandler(console_handler)

    # ── Rotating file: app.log (all levels) ───────────────────────────────────
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(level)
    app_handler.setFormatter(_JsonFormatter())
    root.addHandler(app_handler)

    # ── Rotating file: error.log (ERROR and above only) ───────────────────────
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(_JsonFormatter())
    root.addHandler(error_handler)

    # ── Audit logger: security-relevant events ────────────────────────────────
    audit_logger = logging.getLogger("synapse.audit")
    audit_logger.setLevel(logging.INFO)
    audit_handler = logging.handlers.RotatingFileHandler(
        log_dir / "audit.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    audit_handler.setFormatter(_JsonFormatter())
    audit_logger.addHandler(audit_handler)
    audit_logger.propagate = False  # don't double-log to root

    # ── Quieten noisy third-party libraries ───────────────────────────────────
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "sqlalchemy.pool",
                  "httpx", "httpcore", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging ready — level=%s format=%s log_dir=%s",
        level_name, fmt_mode, log_dir.resolve(),
    )


# ── Audit helper ──────────────────────────────────────────────────────────────

_audit = logging.getLogger("synapse.audit")


def audit(event: str, **kwargs) -> None:
    """Write a structured audit event.

    Usage:
        audit("chat.message", session_id=sid, user_id=uid, field="N_CLEARED")
    """
    _audit.info(event, extra=kwargs)
