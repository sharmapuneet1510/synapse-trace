"""Projects the trace graph into a linear pipeline step sequence."""
from __future__ import annotations
from typing import List, Dict, Any
import networkx as nx
from .subgraph_builder import SubgraphBuilder


class PipelineProjector:
    """Converts a MultiDiGraph into an ordered list of pipeline steps."""

    def project(self, G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """Return an ordered list of pipeline step dicts."""
        order = SubgraphBuilder.linear_pipeline(G)
        steps = []
        for i, node_id in enumerate(order):
            attrs = G.nodes[node_id]
            steps.append({
                "step_id": node_id,
                "order": i + 1,
                "label": attrs.get("label", node_id),
                "type": attrs.get("node_type", "unknown"),
                "transformation_type": attrs.get("transformation_type"),
                "evidence": attrs.get("evidence", {}),
            })
        return steps
