"""Generates plain-English business explanations from trace data."""
from __future__ import annotations
from typing import List
from trace_core.models.common import OriginType
from trace_core.models.trace_models import TraceNode, BranchPath, TraceSummary


class BusinessExplainer:
    """Produces plain-English explanations of field derivation logic."""

    def explain(self, summary: TraceSummary, nodes: List[TraceNode], branches: List[BranchPath]) -> str:
        field = summary.field_name
        origin = summary.origin

        parts = []

        # Origin sentence
        if origin == OriginType.XSLT:
            parts.append(
                f"The field '{field}' originates in an XSLT transformation stylesheet. "
                "It is extracted or mapped from the incoming XML message before any Java processing occurs."
            )
        elif origin == OriginType.JAVA:
            parts.append(
                f"The field '{field}' is derived entirely within Java code. "
                "It is computed, enriched, or assigned during the Java processing pipeline."
            )
        elif origin == OriginType.XSLT_THEN_JAVA:
            parts.append(
                f"The field '{field}' starts its journey in an XSLT stylesheet where it is initially "
                "extracted or mapped. It then flows into the Java layer where it may be further enriched, "
                "overridden, or finalised before appearing in the report."
            )
        else:
            parts.append(
                f"The origin of field '{field}' could not be definitively determined from the available source code."
            )

        # Java enrichment
        java_nodes = [n for n in nodes if n.node_type == "java_method"]
        if java_nodes:
            method_names = [n.evidence.method_or_template_name for n in java_nodes if n.evidence.method_or_template_name]
            if method_names:
                parts.append(
                    f"The field passes through {len(java_nodes)} Java method(s): "
                    f"{', '.join(method_names[:4])}."
                )

        # Branch logic
        condition_nodes = [n for n in nodes if n.metadata.get("conditions")]
        if condition_nodes:
            parts.append(
                f"The field value depends on {len(branches)} conditional outcome(s). "
                "Different business conditions may result in different values being assigned."
            )
            for b in branches[:3]:
                if b.outcome:
                    parts.append(f"  • When {b.condition}: value is set to '{b.outcome}'.")

        # Final assignment
        final_nodes = [n for n in nodes if n.transformation_type and n.transformation_type.value == "FINAL_REPORT_ASSIGNMENT"]
        if final_nodes:
            fn = final_nodes[-1]
            parts.append(
                f"The field is finally assigned to the reporting object in "
                f"'{fn.evidence.class_or_template or 'an output class'}' "
                f"via '{fn.evidence.method_or_template_name or 'a setter method'}'."
            )

        return " ".join(parts)
