"""Extracts method calls from Java method bodies."""
import re
from typing import List, Optional
from modules.trace_core.models.java_models import MethodCall

# Matches patterns like: obj.method(args) or ClassName.method(args) or method(args)
METHOD_CALL_RE = re.compile(
    r"([\w$]+(?:\.[\w$]+)*)\s*\.\s*([\w$]+)\s*\(([^)]*)\)"
    r"|(?<!\.)(?<!\w)([\w$]+)\s*\(([^)]*)\)",
)


class MethodCallExtractor:
    """Extracts method calls from Java source code."""

    def extract(self, method_body: str, line_offset: int = 0) -> List[MethodCall]:
        calls = []
        lines = method_body.splitlines()

        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            for m in METHOD_CALL_RE.finditer(line):
                callee_class: Optional[str]
                callee_method: str
                args_raw: str

                if m.group(1) is not None:
                    full_ref = m.group(1)
                    callee_method = m.group(2)
                    args_raw = m.group(3) or ""
                    parts = full_ref.rsplit(".", 1)
                    callee_class = parts[0] if len(parts) > 1 else full_ref
                else:
                    callee_class = None
                    callee_method = m.group(4) or ""
                    args_raw = m.group(5) or ""

                if not callee_method or callee_method in {
                    "if", "while", "for", "switch", "catch", "new", "return", "throw",
                }:
                    continue

                args = [a.strip() for a in args_raw.split(",") if a.strip()]
                calls.append(MethodCall(
                    callee_class=callee_class,
                    callee_method=callee_method,
                    arguments=args,
                    line_number=line_offset + line_idx + 1,
                    raw_expression=m.group(0).strip(),
                ))

        return calls
