"""Creates NetworkX edge attribute dicts from TraceEdge objects."""
from __future__ import annotations
from typing import Dict, Any
from trace_core.models.trace_models import TraceEdge


class EdgeFactory:
    """Converts TraceEdge objects into NetworkX edge attribute dicts."""

    @staticmethod
    def create(edge: TraceEdge) -> Dict[str, Any]:
        return {
            "relation": edge.relation.value,
            "label": edge.label or edge.relation.value,
            "condition_text": edge.condition_text,
        }
