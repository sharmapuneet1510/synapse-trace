"""Builds a TraceSummary from trace output."""
from __future__ import annotations
from typing import List
from trace_core.models.common import OriginType
from trace_core.models.trace_models import TraceNode, TraceEdge, BranchPath, TraceSummary
from .technical_explainer import TechnicalExplainer
from .business_explainer import BusinessExplainer


class TraceSummarizer:
    """Constructs a TraceSummary from trace nodes, edges, and branches."""

    def __init__(self):
        self._technical = TechnicalExplainer()
        self._business = BusinessExplainer()

    def summarize(
        self,
        field_name: str,
        origin: OriginType,
        nodes: List[TraceNode],
        edges: List[TraceEdge],
        branches: List[BranchPath],
    ) -> TraceSummary:
        has_xslt = any(n.node_type == "xslt_template" for n in nodes)
        has_java = any(n.node_type == "java_method" for n in nodes)

        pipeline_steps = []
        for n in nodes:
            label = n.label
            if label not in pipeline_steps:
                pipeline_steps.append(label)

        tech_explanation = self._technical.explain(nodes, edges, branches)

        # Build a temporary partial summary for business explainer
        partial = TraceSummary(
            field_name=field_name,
            origin=origin,
            pipeline_steps=pipeline_steps,
            branch_count=len(branches),
            total_nodes=len(nodes),
            has_xslt=has_xslt,
            has_java=has_java,
            technical_explanation=tech_explanation,
            business_explanation="",
        )
        business_explanation = self._business.explain(partial, nodes, branches)

        return TraceSummary(
            field_name=field_name,
            origin=origin,
            pipeline_steps=pipeline_steps,
            branch_count=len(branches),
            total_nodes=len(nodes),
            has_xslt=has_xslt,
            has_java=has_java,
            technical_explanation=tech_explanation,
            business_explanation=business_explanation,
        )
