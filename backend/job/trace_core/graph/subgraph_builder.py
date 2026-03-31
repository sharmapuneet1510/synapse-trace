"""Builds presentation subgraphs from the full trace graph."""
from __future__ import annotations
from typing import List, Optional
import networkx as nx


class SubgraphBuilder:
    """Extracts subgraphs for specific views."""

    @staticmethod
    def extract_by_type(G: nx.MultiDiGraph, node_type: str) -> nx.MultiDiGraph:
        """Return a subgraph containing only nodes of the given type."""
        nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == node_type]
        return G.subgraph(nodes).copy()

    @staticmethod
    def extract_by_transformation(G: nx.MultiDiGraph, t_type: str) -> nx.MultiDiGraph:
        """Return a subgraph of nodes with the given transformation type."""
        nodes = [n for n, d in G.nodes(data=True) if d.get("transformation_type") == t_type]
        return G.subgraph(nodes).copy()

    @staticmethod
    def linear_pipeline(G: nx.MultiDiGraph) -> List[str]:
        """Return a topologically sorted node order for pipeline view."""
        try:
            return list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            return list(G.nodes())
