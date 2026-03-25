"""XPath reverse lookup: given a field name, find all XSLT XPaths that reference it."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from ..schemas.field import XPathEntry

# Import stitcher's canonical key builder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from orchestrator.stitcher import _build_match_keys  # noqa: E402


class XPathIndex:
    """Reverse index: field_name -> list of XPath occurrences."""

    def __init__(self):
        self._index: defaultdict[str, list[XPathEntry]] = defaultdict(list)

    def build_from_findings(self, xslt_findings: list) -> None:
        """Build the reverse index from XsltFinding objects."""
        for finding in xslt_findings:
            if finding.finding_type == "value_of" and finding.field_source:
                field_name = self._extract_terminal(finding.field_source)
                if not field_name:
                    continue
                entry = XPathEntry(
                    name=field_name,
                    source=str(finding.meta.file_path) if finding.meta else "",
                    xpath=finding.field_source,
                    template=finding.template_name,
                    output_element=finding.field_target,
                    line=finding.meta.line_number if finding.meta else None,
                )
                for key in _build_match_keys(field_name):
                    self._index[key].append(entry)

            # Also index copy-of / field_mapping findings
            if finding.finding_type == "field_mapping" and finding.field_source:
                field_name = self._extract_terminal(finding.field_source)
                if not field_name:
                    continue
                entry = XPathEntry(
                    name=field_name,
                    source=str(finding.meta.file_path) if finding.meta else "",
                    xpath=finding.field_source,
                    template=finding.template_name,
                    output_element=finding.field_target,
                    line=finding.meta.line_number if finding.meta else None,
                )
                for key in _build_match_keys(field_name):
                    self._index[key].append(entry)

    def lookup(self, field_name: str) -> list[XPathEntry]:
        """Look up all XPaths that reference the given field name."""
        keys = _build_match_keys(field_name)
        results = []
        seen: set[tuple] = set()
        for key in keys:
            for entry in self._index.get(key, []):
                entry_id = (entry.source, entry.xpath, entry.line)
                if entry_id not in seen:
                    seen.add(entry_id)
                    results.append(entry)
        return results

    @staticmethod
    def _extract_terminal(xpath_expr: str) -> str | None:
        """Extract the terminal field name from an XPath expression."""
        if not xpath_expr:
            return None
        # Remove predicates
        cleaned = re.sub(r"\[.*?\]", "", xpath_expr)
        # Get last path segment
        parts = cleaned.split("/")
        last = parts[-1].strip()
        if not last or last in ("*", ".", ".."):
            return None
        # Strip namespace prefix
        if ":" in last:
            last = last.split(":")[-1]
        # Strip @ for attributes
        last = last.lstrip("@")
        return last if last else None
