"""Extracts return statements from Java method bodies."""
import re
from typing import List

RETURN_RE = re.compile(r"\breturn\s+([^;]+)\s*;")


class ReturnExtractor:
    """Finds all return statements in a method body."""

    def extract(self, method_body: str) -> List[str]:
        results = []
        for line in method_body.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            for m in RETURN_RE.finditer(line):
                results.append(m.group(1).strip())
        return results
