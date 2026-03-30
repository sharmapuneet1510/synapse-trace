"""GET /logs/{trace_id} and GET /logs endpoints."""
from __future__ import annotations
import os
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query

router = APIRouter()

_LOG_DIR = "logs"
_LOG_FILES = ["trace.log", "application.log", "error.log"]


def _read_log_lines(path: str, limit: int = 200) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        return []
    lines = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                lines.append(json.loads(raw))
            except json.JSONDecodeError:
                lines.append({"message": raw})
    return lines[-limit:]


@router.get("/{trace_id}", summary="Get logs for a specific trace")
def get_trace_logs(trace_id: str) -> List[Dict[str, Any]]:
    results = []
    for log_file in _LOG_FILES:
        path = os.path.join(_LOG_DIR, log_file)
        for entry in _read_log_lines(path):
            if entry.get("trace_id") == trace_id:
                results.append(entry)
    return results


@router.get("/", summary="Get recent log entries")
def get_recent_logs(limit: int = Query(100, ge=1, le=1000)) -> List[Dict[str, Any]]:
    all_entries = []
    for log_file in _LOG_FILES:
        path = os.path.join(_LOG_DIR, log_file)
        all_entries.extend(_read_log_lines(path, limit=limit))
    return all_entries[-limit:]
