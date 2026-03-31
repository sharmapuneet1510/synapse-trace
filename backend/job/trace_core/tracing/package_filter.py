"""Package filter – decides whether a package should be traced."""
from __future__ import annotations
from typing import List, Dict, Any
from trace_core.utils.pattern_utils import matches_any_pattern

_DEFAULT_EXCLUDES = ["java.*", "javax.*", "org.springframework.*", "sun.*", "com.sun.*"]
_DEFAULT_STOPS = ["org.apache.*"]


class PackageFilter:
    """Determines whether a package should be traced based on config patterns."""

    def __init__(self, config: Dict[str, Any]):
        trace_cfg = config.get("trace", config)
        self._includes: List[str] = trace_cfg.get("includePackages", [])
        self._excludes: List[str] = trace_cfg.get("excludePackages", _DEFAULT_EXCLUDES)
        self._stops: List[str] = trace_cfg.get("stopPackages", _DEFAULT_STOPS)
        self._internal_only: bool = trace_cfg.get("followInternalCallsOnly", True)

    def should_trace(self, package: str) -> bool:
        """Return True if the package should be traced."""
        if not package:
            return False
        # Stop packages are never traced
        if matches_any_pattern(package, self._stops):
            return False
        # Excluded packages are never traced
        if matches_any_pattern(package, self._excludes):
            return False
        # If includes are configured, only trace those
        if self._includes:
            return matches_any_pattern(package, self._includes)
        # If internal-only, accept anything not excluded
        return True
