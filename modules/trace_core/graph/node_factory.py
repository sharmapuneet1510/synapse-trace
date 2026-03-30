"""Creates NetworkX node attribute dicts from TraceNode objects."""
from __future__ import annotations
from typing import Dict, Any
from modules.trace_core.models.trace_models import TraceNode


class NodeFactory:
    """Converts TraceNode objects into NetworkX node attribute dicts."""

    @staticmethod
    def create(node: TraceNode) -> Dict[str, Any]:
        return {
            "label": node.label,
            "node_type": node.node_type,
            "transformation_type": node.transformation_type.value if node.transformation_type else None,
            "evidence": node.evidence.to_dict(),
            **node.metadata,
        }
