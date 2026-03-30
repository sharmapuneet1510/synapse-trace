"""Extracts field assignments relevant to a target field from Java method bodies."""
import re
from typing import List
from modules.trace_core.models.java_models import Assignment
from modules.trace_core.models.common import TransformationType

# Setter pattern: object.setFieldName(...) or object.setFieldName = ...
SETTER_RE = re.compile(r"\.set(\w+)\s*\(([^;]*)\)\s*;?")
# Direct assignment: fieldName = expr;
DIRECT_ASSIGN_RE = re.compile(r"\b(\w+)\s*=\s*([^;=]+)\s*;")


def _to_setter_name(field_name: str) -> str:
    """Convert field name to setter suffix, e.g. N_CLEARED -> NCleared or nCleared."""
    # Try both capitalised forms
    clean = field_name.lstrip("N_").replace("_", "")
    return clean.capitalize()


def _classify(source_expr: str) -> TransformationType:
    src = source_expr.lower()
    if "default" in src or '""' in src or "null" in src:
        return TransformationType.DEFAULTING
    if "override" in src or "overrid" in src:
        return TransformationType.OVERRIDE
    return TransformationType.MAPPING


class AssignmentExtractor:
    """Finds setter calls and direct assignments relevant to a target field."""

    def extract(self, method_body: str, field_name: str) -> List[Assignment]:
        assignments: List[Assignment] = []
        lines = method_body.splitlines()
        setter_suffix = _to_setter_name(field_name)
        field_lower = field_name.lower().replace("_", "").replace("n", "", 1).lower()

        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue

            # Check setter calls
            for m in SETTER_RE.finditer(line):
                name_part = m.group(1)
                value = m.group(2).strip()
                if (name_part.lower() == setter_suffix.lower() or
                        name_part.lower().replace("_", "") == field_lower):
                    assignments.append(Assignment(
                        target_field=f"set{name_part}",
                        source_expression=value,
                        line_number=line_idx + 1,
                        transformation_type=_classify(value),
                    ))

            # Check direct assignments
            for m in DIRECT_ASSIGN_RE.finditer(line):
                lhs = m.group(1)
                rhs = m.group(2).strip()
                if lhs.lower().replace("_", "") == field_name.lower().replace("_", ""):
                    assignments.append(Assignment(
                        target_field=lhs,
                        source_expression=rhs,
                        line_number=line_idx + 1,
                        transformation_type=_classify(rhs),
                    ))

        return assignments
