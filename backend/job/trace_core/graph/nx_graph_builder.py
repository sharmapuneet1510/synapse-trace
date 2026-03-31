"""Builds a NetworkX MultiDiGraph from trace nodes and edges."""
from __future__ import annotations
from typing import List
import networkx as nx
from trace_core.models.trace_models import TraceNode, TraceEdge
from trace_core.logging.logger_factory import LoggerFactory
from .node_factory import NodeFactory
from .edge_factory import EdgeFactory

logger = LoggerFactory.get("trace")


class NxGraphBuilder:
    """Builds a networkx.MultiDiGraph from TraceNode and TraceEdge lists."""

    def build(self, nodes: List[TraceNode], edges: List[TraceEdge]) -> nx.MultiDiGraph:
        """Construct and return a fully attributed MultiDiGraph."""
        G = nx.MultiDiGraph()

        for node in nodes:
            attrs = NodeFactory.create(node)
            G.add_node(node.node_id, **attrs)

        for edge in edges:
            if edge.source_id in G and edge.target_id in G:
                attrs = EdgeFactory.create(edge)
                G.add_edge(edge.source_id, edge.target_id, **attrs)
            else:
                logger.warning(
                    f"Edge references unknown node: {edge.source_id} → {edge.target_id}"
                )

        logger.debug(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
