"""Neo4j-compatible exporter."""
from __future__ import annotations
from typing import Dict, Any
import networkx as nx
from modules.trace_core.graph.graph_exporter import GraphExporter


class Neo4jExporter:
    """Exports a trace graph as Neo4j-compatible Cypher data."""

    def __init__(self):
        self._exporter = GraphExporter()

    def export(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """Return a Neo4j-compatible export payload."""
        return self._exporter.to_neo4j(G)
