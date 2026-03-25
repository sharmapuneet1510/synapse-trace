"""Live event bus for streaming processing progress to dashboards.

Components (scanner, parser, stitcher) emit events as they work.
The dashboard server subscribes and pushes them to the browser via SSE.

Usage:
    from orchestrator.live_events import emit, subscribe

    # In processing code:
    emit("node_added", {"id": "java::class::Foo", "label": "Foo", "type": "JAVA_CLASS"})

    # In dashboard server:
    for event in subscribe():
        yield f"data: {json.dumps(event)}\\n\\n"
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

# Scanner events
SCAN_START = "scan_start"           # project/module scan begins
SCAN_FILE = "scan_file"             # file discovered
SCAN_REF = "scan_ref"               # cross-language ref detected
SCAN_COMPLETE = "scan_complete"     # scan finished

# Parser events
PARSE_START = "parse_start"         # file parsing begins
PARSE_FINDING = "parse_finding"     # finding extracted
PARSE_COMPLETE = "parse_complete"   # file parsing done

# Stitcher events
STITCH_START = "stitch_start"       # stitching begins
NODE_ADDED = "node_added"           # node created in graph
EDGE_ADDED = "edge_added"           # edge created in graph
MATCH_FOUND = "match_found"         # cross-language match found
STITCH_PHASE = "stitch_phase"       # phase transition
STITCH_COMPLETE = "stitch_complete" # stitching done

# Trace events
TRACE_START = "trace_start"         # trace operation begins
LIB_SEARCH = "lib_search"           # searching library for class
LIB_FOUND = "lib_found"             # class found in library
FILTER_START = "filter_start"       # subgraph filtering begins
FILTER_COMPLETE = "filter_complete" # filtering done
TRACE_COMPLETE = "trace_complete"   # trace operation complete

# Stats
STATS_UPDATE = "stats_update"       # periodic stats snapshot


# ---------------------------------------------------------------------------
# Event bus
# ---------------------------------------------------------------------------

@dataclass
class TraceEvent:
    event_type: str
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "event": self.event_type,
            "data": self.data,
            "ts": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class EventBus:
    """Thread-safe event bus with subscriber support."""

    def __init__(self, max_history: int = 5000) -> None:
        self._lock = threading.Lock()
        self._subscribers: list[deque] = []
        self._history: deque[TraceEvent] = deque(maxlen=max_history)
        self._enabled = False
        # Counters
        self.stats = {
            "files_scanned": 0,
            "java_findings": 0,
            "xslt_findings": 0,
            "nodes_created": 0,
            "edges_created": 0,
            "matches_found": 0,
            "libs_searched": 0,
            "classes_resolved": 0,
        }

    def enable(self) -> None:
        """Enable event emission. Off by default to avoid overhead."""
        self._enabled = True
        logger.info("Live event bus enabled")

    def disable(self) -> None:
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def emit(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Emit an event to all subscribers."""
        if not self._enabled:
            return

        event = TraceEvent(event_type=event_type, data=data or {})

        # Update counters
        self._update_stats(event_type, data or {})

        with self._lock:
            self._history.append(event)
            for q in self._subscribers:
                q.append(event)

    def subscribe(self, include_history: bool = True) -> Generator[TraceEvent, None, None]:
        """Subscribe to events. Yields events as they arrive."""
        q: deque[TraceEvent] = deque()

        with self._lock:
            if include_history:
                q.extend(self._history)
            self._subscribers.append(q)

        try:
            while True:
                if q:
                    yield q.popleft()
                else:
                    time.sleep(0.05)  # 50ms poll
        finally:
            with self._lock:
                self._subscribers.remove(q)

    def get_history(self) -> list[dict]:
        """Get all historical events as dicts."""
        with self._lock:
            return [e.to_dict() for e in self._history]

    def get_stats(self) -> dict:
        """Get current processing stats."""
        return dict(self.stats)

    def reset(self) -> None:
        """Clear history and reset counters."""
        with self._lock:
            self._history.clear()
            for k in self.stats:
                self.stats[k] = 0

    def _update_stats(self, event_type: str, data: dict) -> None:
        if event_type == SCAN_FILE:
            self.stats["files_scanned"] += 1
        elif event_type == PARSE_FINDING:
            if data.get("parser") == "xslt":
                self.stats["xslt_findings"] += 1
            else:
                self.stats["java_findings"] += 1
        elif event_type == NODE_ADDED:
            self.stats["nodes_created"] += 1
        elif event_type == EDGE_ADDED:
            self.stats["edges_created"] += 1
        elif event_type == MATCH_FOUND:
            self.stats["matches_found"] += 1
        elif event_type == LIB_SEARCH:
            self.stats["libs_searched"] += 1
        elif event_type == LIB_FOUND:
            self.stats["classes_resolved"] += 1


# ---------------------------------------------------------------------------
# Global instance & convenience functions
# ---------------------------------------------------------------------------

_bus = EventBus()


def get_bus() -> EventBus:
    """Get the global event bus."""
    return _bus


def emit(event_type: str, data: dict[str, Any] | None = None) -> None:
    """Emit an event on the global bus."""
    _bus.emit(event_type, data)


def subscribe(include_history: bool = True) -> Generator[TraceEvent, None, None]:
    """Subscribe to events on the global bus."""
    return _bus.subscribe(include_history)


def enable() -> None:
    """Enable live event emission."""
    _bus.enable()


def disable() -> None:
    """Disable live event emission."""
    _bus.disable()


def reset() -> None:
    """Reset the event bus."""
    _bus.reset()


def stats() -> dict:
    """Get current stats."""
    return _bus.get_stats()
