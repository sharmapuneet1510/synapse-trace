"""Traces a field through XSLT templates."""
from __future__ import annotations
import uuid
from typing import List, Tuple, Optional, Dict, Set, TYPE_CHECKING
from modules.trace_core.models.common import Evidence, TransformationType, EdgeRelationType
from modules.trace_core.models.trace_models import TraceNode, TraceEdge
from modules.trace_core.models.xslt_models import XsltTemplate
from modules.trace_core.logging.context_logger import ContextLogger
from modules.trace_core.tracing.trace_context import TraceContext
from modules.trace_core.tracing.recursion_guard import RecursionGuard
from modules.trace_core.tracing.evidence_builder import EvidenceBuilder
from modules.trace_core.tracing.transformation_classifier import TransformationClassifier

if TYPE_CHECKING:
    from modules.trace_core.parsers.xslt.template_registry import TemplateRegistry


class XsltTraceEngine:
    """Traces a field through XSLT template chains."""

    def __init__(self, template_registry: "TemplateRegistry"):
        self._registry = template_registry
        self._classifier = TransformationClassifier()

    def find_field_templates(self, field_name: str) -> List[XsltTemplate]:
        """Find templates that reference the given field."""
        results = []
        field_variants = {
            field_name.upper(),
            field_name.lower(),
            field_name.replace("_", "").lower(),
            field_name.replace("N_", "").lower(),
        }
        for tmpl in self._registry.all_templates():
            # Check output mappings
            for om in tmpl.output_mappings:
                if om.field_name.upper() in field_variants or field_name.upper() in om.field_name.upper():
                    results.append(tmpl)
                    break
            else:
                # Check raw XML for field name mentions
                if tmpl.raw_xml and any(v in (tmpl.raw_xml or "").lower() for v in field_variants):
                    results.append(tmpl)
        return results

    def trace_field(self, field_name: str, ctx: TraceContext) -> Tuple[List[TraceNode], List[TraceEdge]]:
        """Trace a field through all matching XSLT templates."""
        logger = ContextLogger("trace", trace_id=ctx.trace_id, field_name=field_name)
        nodes: List[TraceNode] = []
        edges: List[TraceEdge] = []

        entry_templates = self.find_field_templates(field_name)
        logger.info(f"XSLT trace: found {len(entry_templates)} entry templates for field '{field_name}'")

        for tmpl in entry_templates:
            t_nodes, t_edges = self.trace_template(tmpl, ctx)
            nodes.extend(t_nodes)
            edges.extend(t_edges)

        return nodes, edges

    def trace_template(
        self,
        template: XsltTemplate,
        ctx: TraceContext,
        parent_node_id: Optional[str] = None,
    ) -> Tuple[List[TraceNode], List[TraceEdge]]:
        logger = ContextLogger("trace", trace_id=ctx.trace_id, field_name=ctx.field_name)
        nodes: List[TraceNode] = []
        edges: List[TraceEdge] = []

        node_id = f"xslt:{template.name}:{template.file_path}"
        if RecursionGuard.is_visited(node_id, ctx):
            logger.debug(f"XSLT loop prevention – skipping already visited template: {template.name}", template_name=template.name)
            return nodes, edges
        if not RecursionGuard.check_depth(ctx):
            return nodes, edges

        RecursionGuard.mark_visited(node_id, ctx)

        t_type = self._classifier.classify(template.name)
        evidence = EvidenceBuilder.from_xslt_template(template, transformation_type=t_type)
        node = TraceNode(
            node_id=node_id,
            label=f"XSLT: {template.name}",
            node_type="xslt_template",
            transformation_type=t_type,
            evidence=evidence,
            metadata={
                "variables": [v.to_dict() for v in template.variables],
                "params": [p.to_dict() for p in template.params],
                "conditions": [c.to_dict() for c in template.conditions],
            },
        )
        nodes.append(node)

        if parent_node_id:
            edges.append(TraceEdge(
                source_id=parent_node_id,
                target_id=node_id,
                relation=EdgeRelationType.CALLS,
                label="calls",
            ))

        # Follow call-template chains
        for ct in template.call_templates:
            resolved = self._registry.find(ct.name)
            if resolved:
                child_nodes, child_edges = self.trace_template(resolved, ctx.descend(), parent_node_id=node_id)
                nodes.extend(child_nodes)
                edges.extend(child_edges)
            else:
                logger.warning(f"Unresolved call-template: {ct.name}", template_name=ct.name)

        return nodes, edges
