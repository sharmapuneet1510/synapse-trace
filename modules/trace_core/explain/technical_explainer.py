"""Generates technical explanations from trace nodes."""
from __future__ import annotations
from typing import List
from modules.trace_core.models.trace_models import TraceNode, TraceEdge, BranchPath


class TechnicalExplainer:
    """Produces a technical step-by-step explanation from trace data."""

    def explain(self, nodes: List[TraceNode], edges: List[TraceEdge], branches: List[BranchPath]) -> str:
        if not nodes:
            return "No lineage trace data found for this field."

        lines = ["=== Technical Lineage Trace ===\n"]

        xslt_nodes = [n for n in nodes if n.node_type == "xslt_template"]
        java_nodes = [n for n in nodes if n.node_type == "java_method"]

        if xslt_nodes:
            lines.append("[ XSLT Phase ]")
            for i, n in enumerate(xslt_nodes, 1):
                ev = n.evidence
                loc = f"{ev.file_path}:{ev.line_number}" if ev.file_path else "unknown location"
                lines.append(f"  {i}. {n.label}")
                lines.append(f"     Location: {loc}")
                if n.transformation_type:
                    lines.append(f"     Type: {n.transformation_type.value}")
                conds = n.metadata.get("conditions", [])
                if conds:
                    lines.append(f"     Conditions: {', '.join(c.get('condition_text','') for c in conds[:2])}")

        if java_nodes:
            lines.append("\n[ Java Phase ]")
            for i, n in enumerate(java_nodes, 1):
                ev = n.evidence
                loc = f"{ev.class_or_template}.{ev.method_or_template_name}()"
                file_loc = f" [{ev.file_path}:{ev.line_number}]" if ev.file_path else ""
                lines.append(f"  {i}. {loc}{file_loc}")
                if n.transformation_type:
                    lines.append(f"     Type: {n.transformation_type.value}")
                conds = n.metadata.get("conditions", [])
                if conds:
                    lines.append(f"     Conditions: {'; '.join(c.get('condition_text','') for c in conds[:2])}")
                assigns = n.metadata.get("assignments", [])
                if assigns:
                    for a in assigns[:2]:
                        lines.append(f"     Assigns: {a.get('target_field')} = {a.get('source_expression','')[:60]}")

        if branches:
            lines.append(f"\n[ Branch Analysis – {len(branches)} branches ]")
            for b in branches[:5]:
                lines.append(f"  Branch: {b.condition}")
                if b.outcome:
                    lines.append(f"    Outcome: {b.outcome}")

        return "\n".join(lines)
