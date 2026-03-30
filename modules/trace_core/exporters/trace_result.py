"""TraceResult – the primary output object of every trace invocation."""
from __future__ import annotations
import json
from typing import List, Dict, Any, Optional
import networkx as nx
from modules.trace_core.models.trace_models import TraceNode, TraceEdge, BranchPath, TraceSummary
from modules.trace_core.models.common import Evidence
from modules.trace_core.graph.graph_exporter import GraphExporter
from modules.trace_core.exporters.html_exporter import HtmlExporter
from modules.trace_core.exporters.neo4j_exporter import Neo4jExporter


class TraceResult:
    """Encapsulates the complete output of a field lineage trace.

    Provides export helpers:
        trace_result.to_graph()
        trace_result.to_json()
        trace_result.to_pipeline_json()
        trace_result.to_branch_json()
        trace_result.to_html()
        trace_result.to_neo4j()
    """

    def __init__(
        self,
        field_name: str,
        trace_id: str,
        summary: TraceSummary,
        graph: nx.MultiDiGraph,
        nodes: List[TraceNode],
        edges: List[TraceEdge],
        branches: List[BranchPath],
        metadata: Dict[str, Any],
        evidence_list: List[Evidence],
    ):
        self.field_name = field_name
        self.trace_id = trace_id
        self.summary = summary
        self.graph = graph
        self.nodes = nodes
        self.edges = edges
        self.branches = branches
        self.metadata = metadata
        self.evidence_list = evidence_list
        self._graph_exporter = GraphExporter()
        self._html_exporter = HtmlExporter()
        self._neo4j_exporter = Neo4jExporter()

    # ------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------

    def to_graph(self) -> nx.MultiDiGraph:
        """Return the underlying NetworkX MultiDiGraph."""
        return self.graph

    def to_json(self) -> Dict[str, Any]:
        """Return the canonical serialized trace result."""
        return {
            "trace_id": self.trace_id,
            "field_name": self.field_name,
            "summary": self.summary.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "branches": [b.to_dict() for b in self.branches],
            "evidence": [e.to_dict() for e in self.evidence_list],
            "graph_json": self._graph_exporter.to_json(self.graph),
            "metadata": self.metadata,
        }

    def to_pipeline_json(self) -> Dict[str, Any]:
        """Return pipeline-optimized view data."""
        return {
            "trace_id": self.trace_id,
            "field_name": self.field_name,
            "origin": self.summary.origin.value,
            **self._graph_exporter.to_pipeline_json(self.graph),
        }

    def to_branch_json(self) -> Dict[str, Any]:
        """Return branch/mind-map-optimized view data."""
        return {
            "trace_id": self.trace_id,
            "field_name": self.field_name,
            **self._graph_exporter.to_branch_json(self.branches),
        }

    def to_html(self) -> str:
        """Return a self-contained HTML report."""
        return self._html_exporter.export(self.summary, self.nodes, self.branches)

    def to_neo4j(self) -> Dict[str, Any]:
        """Return a Neo4j-compatible export payload."""
        return self._neo4j_exporter.export(self.graph)

    def __repr__(self) -> str:
        return (
            f"TraceResult(field={self.field_name!r}, trace_id={self.trace_id!r}, "
            f"nodes={len(self.nodes)}, branches={len(self.branches)})"
        )
