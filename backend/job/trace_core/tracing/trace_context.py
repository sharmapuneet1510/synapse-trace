"""TraceContext – carries per-trace state through the tracing pipeline."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict, Any


@dataclass
class TraceContext:
    trace_id: str
    field_name: str
    jurisdiction: Optional[str] = None
    package_filters: List[str] = field(default_factory=list)
    max_depth: int = 20
    current_depth: int = 0
    visited_nodes: Set[str] = field(default_factory=set)
    config: Dict[str, Any] = field(default_factory=dict)
    enable_condition_tracing: bool = True
    enable_xslt_imports: bool = True

    def descend(self) -> "TraceContext":
        """Return a copy with depth incremented."""
        return TraceContext(
            trace_id=self.trace_id,
            field_name=self.field_name,
            jurisdiction=self.jurisdiction,
            package_filters=list(self.package_filters),
            max_depth=self.max_depth,
            current_depth=self.current_depth + 1,
            visited_nodes=self.visited_nodes,  # shared reference intentional
            config=self.config,
            enable_condition_tracing=self.enable_condition_tracing,
            enable_xslt_imports=self.enable_xslt_imports,
        )

    @property
    def depth_exceeded(self) -> bool:
        return self.current_depth >= self.max_depth
