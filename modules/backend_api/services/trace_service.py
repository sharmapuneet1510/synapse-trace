"""API-level trace service – wraps trace_core TraceService."""
from __future__ import annotations
import functools
from typing import Optional, List
from modules.trace_core.tracing.trace_service import TraceService
from modules.trace_core.exporters.trace_result import TraceResult
from modules.trace_core.logging.logger_factory import LoggerFactory

logger = LoggerFactory.get("api")


class ApiTraceService:
    """Singleton wrapper around the trace_core TraceService for API use."""

    _instance: Optional["ApiTraceService"] = None
    _trace_service: Optional[TraceService] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_service(self) -> TraceService:
        if self._trace_service is None:
            logger.info("Initialising TraceService for API layer")
            self._trace_service = TraceService()
        return self._trace_service

    def trace(
        self,
        field_name: str,
        jurisdiction: Optional[str] = None,
        package_filters: Optional[List[str]] = None,
        max_depth: int = 20,
        enable_condition_tracing: bool = True,
        enable_xslt_imports: bool = True,
    ) -> TraceResult:
        logger.info(f"API trace request for field: {field_name}", field_name=field_name)
        return self._get_service().trace(
            field_name=field_name,
            jurisdiction=jurisdiction,
            package_filters=package_filters,
            max_depth=max_depth,
            enable_condition_tracing=enable_condition_tracing,
            enable_xslt_imports=enable_xslt_imports,
        )
