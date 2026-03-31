"""Deep Java call-chain tracer."""
from __future__ import annotations
import re
from typing import List, Tuple, Optional, Dict, TYPE_CHECKING
from trace_core.models.common import Evidence, TransformationType, EdgeRelationType
from trace_core.models.trace_models import TraceNode, TraceEdge
from trace_core.models.java_models import JavaClass, JavaMethod
from trace_core.logging.context_logger import ContextLogger
from trace_core.tracing.trace_context import TraceContext
from trace_core.tracing.recursion_guard import RecursionGuard
from trace_core.tracing.package_filter import PackageFilter
from trace_core.tracing.evidence_builder import EvidenceBuilder
from trace_core.tracing.transformation_classifier import TransformationClassifier
from trace_core.parsers.java.symbol_resolver import SymbolResolver

SETTER_RE = re.compile(r"\.set([A-Z]\w*)\s*\(")
FINAL_REPORT_RE = re.compile(r"report\.|output\.|result\.", re.IGNORECASE)


class JavaTraceEngine:
    """Recursively traces Java method call chains for a target field."""

    def __init__(self, java_index: Dict[str, JavaClass], config: dict):
        self._index = java_index
        self._filter = PackageFilter(config)
        self._classifier = TransformationClassifier()
        self._resolver = SymbolResolver()

    def find_field_entry_methods(self, field_name: str) -> List[Tuple[JavaClass, JavaMethod]]:
        """Find Java methods that directly set or reference the target field."""
        results = []
        field_variants = {
            field_name.upper(),
            field_name.lower(),
            field_name.replace("_", ""),
            field_name.replace("N_", ""),
        }
        setter_suffix = field_name.replace("N_", "").replace("_", "").lower()

        for fqn, cls in self._index.items():
            if not self._filter.should_trace(cls.package):
                continue
            for method in cls.methods:
                body = method.body_text.lower()
                if any(v.lower() in body for v in field_variants) or setter_suffix in body:
                    results.append((cls, method))

        return results

    def trace_field(self, field_name: str, ctx: TraceContext) -> Tuple[List[TraceNode], List[TraceEdge]]:
        logger = ContextLogger("trace", trace_id=ctx.trace_id, field_name=field_name)
        nodes: List[TraceNode] = []
        edges: List[TraceEdge] = []

        entry_points = self.find_field_entry_methods(field_name)
        logger.info(f"Java trace: found {len(entry_points)} entry methods for field '{field_name}'")

        for cls, method in entry_points:
            m_nodes, m_edges = self.trace_method(cls, method, ctx)
            nodes.extend(m_nodes)
            edges.extend(m_edges)

        return nodes, edges

    def trace_method(
        self,
        cls: JavaClass,
        method: JavaMethod,
        ctx: TraceContext,
        parent_node_id: Optional[str] = None,
    ) -> Tuple[List[TraceNode], List[TraceEdge]]:
        logger = ContextLogger("trace", trace_id=ctx.trace_id, field_name=ctx.field_name)
        nodes: List[TraceNode] = []
        edges: List[TraceEdge] = []

        node_id = f"java:{cls.fqn}.{method.name}"
        if RecursionGuard.is_visited(node_id, ctx):
            logger.debug(f"Java loop prevention – skipping: {node_id}", method_name=method.name)
            return nodes, edges
        if not RecursionGuard.check_depth(ctx):
            return nodes, edges

        RecursionGuard.mark_visited(node_id, ctx)

        is_final = bool(FINAL_REPORT_RE.search(method.name)) or any(
            bool(FINAL_REPORT_RE.search(a.target_field)) for a in method.assignments
        )
        t_type = self._classifier.classify(method.name, method.body_text, is_final_setter=is_final)

        # Build condition text from field-relevant conditions
        cond_text = None
        if method.conditions:
            cond_text = " | ".join(c.condition_text for c in method.conditions[:3])

        evidence = EvidenceBuilder.from_java_method(cls, method, t_type, cond_text)
        node = TraceNode(
            node_id=node_id,
            label=f"{cls.simple_name}.{method.name}()",
            node_type="java_method",
            transformation_type=t_type,
            evidence=evidence,
            metadata={
                "conditions": [c.to_dict() for c in method.conditions],
                "assignments": [a.to_dict() for a in method.assignments],
                "return_type": method.return_type,
            },
        )
        nodes.append(node)

        if parent_node_id:
            edges.append(TraceEdge(
                source_id=parent_node_id,
                target_id=node_id,
                relation=EdgeRelationType.CALLS,
            ))

        # Recurse into called methods that match package filter
        for call in method.method_calls:
            if not call.callee_class:
                continue
            callee_fqn = self._resolver.resolve(call, cls, self._index)
            if not callee_fqn:
                continue
            callee_cls = self._index.get(callee_fqn)
            if not callee_cls:
                continue
            if not self._filter.should_trace(callee_cls.package):
                continue

            callee_method = callee_cls.get_method(call.callee_method)
            if not callee_method:
                continue

            child_nodes, child_edges = self.trace_method(callee_cls, callee_method, ctx.descend(), parent_node_id=node_id)
            nodes.extend(child_nodes)
            edges.extend(child_edges)

        return nodes, edges
