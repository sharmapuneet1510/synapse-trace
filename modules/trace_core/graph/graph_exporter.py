"""Converts NetworkX graphs to UI-ready and Neo4j-compatible JSON."""
from __future__ import annotations
from typing import List, Dict, Any
import networkx as nx
from modules.trace_core.models.trace_models import BranchPath
from .pipeline_projector import PipelineProjector
from .branch_projector import BranchProjector


class GraphExporter:
    """Exports graphs to various JSON formats."""

    def __init__(self):
        self._pipeline_projector = PipelineProjector()
        self._branch_projector = BranchProjector()

    def to_json(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """Full graph as node/edge JSON."""
        nodes = [{"id": n, **d} for n, d in G.nodes(data=True)]
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({"source": u, "target": v, **data})
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "node_count": G.number_of_nodes(),
                "edge_count": G.number_of_edges(),
            },
        }

    def to_pipeline_json(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        steps = self._pipeline_projector.project(G)
        return {"steps": steps, "total_steps": len(steps)}

    def to_branch_json(self, branches: List[BranchPath]) -> Dict[str, Any]:
        return self._branch_projector.project(branches)

    def to_neo4j(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """Return Neo4j-compatible Cypher statements and data."""
        cypher_nodes = []
        cypher_rels = []
        nodes = []
        relationships = []

        for node_id, attrs in G.nodes(data=True):
            t_type = attrs.get("node_type", "Node").replace("_", "").title()
            props = {k: v for k, v in attrs.items() if isinstance(v, (str, int, float, bool))}
            props["id"] = node_id
            nodes.append({"id": node_id, "label": t_type, "properties": props})
            escaped_id = node_id.replace("'", "\\'")
            prop_str = ", ".join(f"{k}: '{v}'" for k, v in props.items())
            cypher_nodes.append(f"MERGE (n:{t_type} {{id: '{escaped_id}', {prop_str}}})")

        for u, v, data in G.edges(data=True):
            rel_type = data.get("relation", "FLOWS_TO").upper().replace(" ", "_")
            relationships.append({"source": u, "target": v, "type": rel_type, "properties": data})
            cypher_rels.append(
                f"MATCH (a {{id: '{u}'}}), (b {{id: '{v}'}}) "
                f"MERGE (a)-[:{rel_type}]->(b)"
            )

        return {
            "nodes": nodes,
            "relationships": relationships,
            "cypher_statements": cypher_nodes + cypher_rels,
        }
