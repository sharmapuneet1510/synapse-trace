"""Context-aware logger that auto-injects trace_id and field_name into every entry."""
import logging
from typing import Optional
from .logger_factory import LoggerFactory


class ContextLogger:
    """Wraps a standard logger and injects trace context into every record."""

    def __init__(self, name: str, trace_id: Optional[str] = None, field_name: Optional[str] = None):
        self._logger = LoggerFactory.get(name)
        self.trace_id = trace_id
        self.field_name = field_name

    def _extra(self, extra: dict) -> dict:
        base = {}
        if self.trace_id:
            base["trace_id"] = self.trace_id
        if self.field_name:
            base["field_name"] = self.field_name
        base.update(extra)
        return base

    def debug(self, msg: str, **extra):
        self._logger.debug(msg, extra=self._extra(extra))

    def info(self, msg: str, **extra):
        self._logger.info(msg, extra=self._extra(extra))

    def warning(self, msg: str, **extra):
        self._logger.warning(msg, extra=self._extra(extra))

    def error(self, msg: str, exc_info=False, **extra):
        self._logger.error(msg, exc_info=exc_info, extra=self._extra(extra))

    def exception(self, msg: str, **extra):
        self._logger.exception(msg, extra=self._extra(extra))
