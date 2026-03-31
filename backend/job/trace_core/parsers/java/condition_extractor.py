"""Extracts conditional structures from Java method bodies."""
import re
from typing import List
from trace_core.models.java_models import Condition

IF_RE = re.compile(r"\bif\s*\(([^)]+)\)", re.MULTILINE)
ELSE_IF_RE = re.compile(r"\belse\s+if\s*\(([^)]+)\)", re.MULTILINE)
TERNARY_RE = re.compile(r"([^?;]+)\s*\?\s*([^:]+)\s*:\s*([^;]+)\s*;")
NULL_CHECK_RE = re.compile(r"\b(\w+)\s*(?:==|!=)\s*null\b")
SWITCH_RE = re.compile(r"\bswitch\s*\(([^)]+)\)")


class ConditionExtractor:
    """Extracts if/else/switch/ternary conditions from Java source."""

    def extract(self, method_body: str) -> List[Condition]:
        conditions: List[Condition] = []
        lines = method_body.splitlines()

        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            lineno = line_idx + 1

            for m in ELSE_IF_RE.finditer(line):
                conditions.append(Condition(
                    condition_text=m.group(1).strip(),
                    branch_type="else_if",
                    line_number=lineno,
                ))

            for m in IF_RE.finditer(line):
                text = m.group(1).strip()
                if not any(c.condition_text == text and c.line_number == lineno for c in conditions):
                    conditions.append(Condition(
                        condition_text=text,
                        branch_type="if",
                        line_number=lineno,
                    ))

            for m in SWITCH_RE.finditer(line):
                conditions.append(Condition(
                    condition_text=f"switch({m.group(1).strip()})",
                    branch_type="switch",
                    line_number=lineno,
                ))

            for m in TERNARY_RE.finditer(line):
                cond = m.group(1).strip().split("=")[-1].strip()
                conditions.append(Condition(
                    condition_text=cond,
                    branch_type="ternary",
                    line_number=lineno,
                    true_branch=m.group(2).strip(),
                    false_branch=m.group(3).strip(),
                ))

        return conditions
