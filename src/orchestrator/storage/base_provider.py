"""Abstract base class for graph storage providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from orchestrator.models import LineageEdge, LineageNode, StitchedLineage


class BaseGraphProvider(ABC):
    """Plugin interface for graph storage backends.

    Providers implement add_node, add_edge, persist, and export_node_link_json.
    The ingest_lineage convenience method is provided for free.
    """

    @abstractmethod
    def add_node(self, node: LineageNode) -> None: ...

    @abstractmethod
    def add_edge(self, edge: LineageEdge) -> None: ...

    @abstractmethod
    def persist(self) -> None:
        """Flush the graph to the backing store."""

    @abstractmethod
    def export_node_link_json(self) -> dict:
        """Return a Node-Link schema dict compatible with Neo4j APOC import."""

    def ingest_lineage(self, lineage: StitchedLineage) -> None:
        """Bulk load a StitchedLineage into this provider."""
        for node in lineage.nodes:
            self.add_node(node)
        for edge in lineage.edges:
            self.add_edge(edge)
