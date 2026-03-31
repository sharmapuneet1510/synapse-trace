"""In-memory cache for parsed jurisdiction results."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class JurisdictionCache:
    jurisdiction_id: str
    java_findings: list = field(default_factory=list)
    xslt_findings: list = field(default_factory=list)
    lineage: Any = None
    xpath_index: dict = field(default_factory=dict)
    parsed_at: datetime | None = None
    status: str = "pending"  # pending | parsing | ready | error
    error: str | None = None


class ParseCache:
    """Thread-safe cache for parsed results per jurisdiction."""

    def __init__(self):
        self._lock = threading.Lock()
        self._store: dict[str, JurisdictionCache] = {}
        self.batch_status: str = "idle"  # idle | running | done | error
        self.batch_started: datetime | None = None
        self.batch_completed: datetime | None = None
        self.logs: list[dict] = []

    def get(self, jurisdiction_id: str) -> JurisdictionCache | None:
        with self._lock:
            return self._store.get(jurisdiction_id)

    def set(self, jurisdiction_id: str, cache: JurisdictionCache):
        with self._lock:
            prev = self._store.get(jurisdiction_id)
            self._store[jurisdiction_id] = cache
        if prev is None:
            logger.debug("Cache entry created for jurisdiction '%s'", jurisdiction_id)
        elif prev.status != cache.status:
            logger.info(
                "Cache status changed for '%s': %s → %s",
                jurisdiction_id, prev.status, cache.status,
            )

    def all_ids(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def add_log(self, level: str, message: str, jurisdiction_id: str | None = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "jurisdiction_id": jurisdiction_id,
        }
        with self._lock:
            self.logs.append(entry)
            # Keep last 500 log entries
            if len(self.logs) > 500:
                self.logs = self.logs[-500:]

        # Mirror to Python logging so entries appear in server output too
        prefix = f"[{jurisdiction_id}] " if jurisdiction_id else ""
        log_fn = {
            "info": logger.info,
            "debug": logger.debug,
            "warn": logger.warning,
            "warning": logger.warning,
            "error": logger.error,
        }.get(level, logger.info)
        log_fn("%s%s", prefix, message)

    def get_logs(self, limit: int = 100) -> list[dict]:
        with self._lock:
            return list(self.logs[-limit:])

    def clear(self):
        with self._lock:
            self._store.clear()
            self.logs.clear()


# Singleton
parse_cache = ParseCache()
