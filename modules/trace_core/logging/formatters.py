"""Structured JSON log formatter."""
import json
import logging
import traceback
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """Emits each log record as a single-line JSON object."""

    FIELDS = [
        "trace_id", "field_name", "jurisdiction",
        "repository", "module_name", "package_name",
        "class_name", "method_name", "template_name",
        "recursion_depth", "condition",
    ]

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        for f in self.FIELDS:
            val = getattr(record, f, None)
            if val is not None:
                entry[f] = val

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            entry["exception"] = record.exc_text

        return json.dumps(entry, default=str)
