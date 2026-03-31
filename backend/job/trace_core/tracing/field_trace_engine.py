"""Orchestrates XSLT + Java tracing for a single field."""
from __future__ import annotations
from typing import List, Tuple, Dict, TYPE_CHECKING
from trace_core.models.common import OriginType, EdgeRelationType, Evidence
from trace_core.models.trace_models import TraceNode, TraceEdge
from trace_core.logging.context_logger import ContextLogger
from .trace_context import TraceContext
from .xslt_trace_engine import XsltTraceEngine
from .java_trace_engine import JavaTraceEngine

if TYPE_CHECKING:
    from trace_core.indexers.repo_indexer import Index


class FieldTraceEngine:
    """Determines origin and orchestrates full field-level trace."""

    def __init__(self, index: "Index", config: dict):
        self._index = index
        self._config = config
        self._xslt_engine = XsltTraceEngine(index.xslt_templates)
        self._java_engine = JavaTraceEngine(index.java_classes, config)

    def detect_origin(self, field_name: str, ctx: TraceContext) -> OriginType:
        logger = ContextLogger("trace", trace_id=ctx.trace_id, field_name=field_name)
        xslt_templates = self._xslt_engine.find_field_templates(field_name)
        java_methods = self._java_engine.find_field_entry_methods(field_name)

        logger.info(
            f"Origin detection: {len(xslt_templates)} XSLT templates, {len(java_methods)} Java methods"
        )

        if xslt_templates and java_methods:
            return OriginType.XSLT_THEN_JAVA
        if xslt_templates:
            return OriginType.XSLT
        if java_methods:
            return OriginType.JAVA
        return OriginType.UNKNOWN

    def trace(
        self, field_name: str, ctx: TraceContext
    ) -> Tuple[List[TraceNode], List[TraceEdge], OriginType]:
        logger = ContextLogger("trace", trace_id=ctx.trace_id, field_name=field_name)
        nodes: List[TraceNode] = []
        edges: List[TraceEdge] = []

        origin = self.detect_origin(field_name, ctx)
        logger.info(f"Field '{field_name}' origin detected as: {origin.value}")

        if origin in (OriginType.XSLT, OriginType.XSLT_THEN_JAVA):
            x_nodes, x_edges = self._xslt_engine.trace_field(field_name, ctx)
            nodes.extend(x_nodes)
            edges.extend(x_edges)
            logger.info(f"XSLT phase: {len(x_nodes)} nodes, {len(x_edges)} edges")

        if origin in (OriginType.JAVA, OriginType.XSLT_THEN_JAVA):
            j_nodes, j_edges = self._java_engine.trace_field(field_name, ctx)

            # Link last XSLT node to first Java node
            if nodes and j_nodes:
                edges.append(TraceEdge(
                    source_id=nodes[-1].node_id,
                    target_id=j_nodes[0].node_id,
                    relation=EdgeRelationType.FLOWS_TO,
                    label="XSLT→Java",
                ))

            nodes.extend(j_nodes)
            edges.extend(j_edges)
            logger.info(f"Java phase: {len(j_nodes)} nodes, {len(j_edges)} edges")

        # ── Connect disconnected roots via a synthetic field-origin node ──────
        # After tracing, some entry-point nodes may still have no incoming edge
        # (they were found independently by find_field_entry_methods but were
        # not reached via recursion from another entry point).  Emit a
        # synthetic root node representing the field itself and wire all such
        # orphan roots to it so the graph is fully connected.
        nodes, edges = self._connect_orphan_roots(field_name, nodes, edges)

        logger.info(f"Trace complete: {len(nodes)} total nodes, {len(edges)} total edges")
        return nodes, edges, origin

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _connect_orphan_roots(
        self,
        field_name: str,
        nodes: List[TraceNode],
        edges: List[TraceEdge],
    ) -> Tuple[List[TraceNode], List[TraceEdge]]:
        """Ensure every node is reachable from a single root.

        Nodes that have no incoming edge are *orphan roots*.  If there is more
        than one, we insert a synthetic ``field`` node at the top and connect
        all orphan roots to it so the rendered DAG has a single entry point.
        """
        if not nodes:
            return nodes, edges

        # Build set of node IDs that are edge targets (have at least one parent)
        target_ids = {e.target_id for e in edges}
        orphans = [n for n in nodes if n.node_id not in target_ids]

        # Nothing to do: zero or one orphan (already a single root)
        if len(orphans) <= 1:
            return nodes, edges

        # Create a synthetic root representing the field itself
        root_id = f"field:{field_name}"
        root_node = TraceNode(
            node_id=root_id,
            label=field_name,
            node_type="field",
            transformation_type=None,
            evidence=Evidence(),
            metadata={"synthetic": True},
        )

        root_edges = [
            TraceEdge(
                source_id=root_id,
                target_id=orphan.node_id,
                relation=EdgeRelationType.FLOWS_TO,
                label="originates",
            )
            for orphan in orphans
        ]

        return [root_node] + nodes, root_edges + edges
