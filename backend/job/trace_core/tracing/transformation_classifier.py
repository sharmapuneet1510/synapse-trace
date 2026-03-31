"""Classifies trace steps into TransformationType values."""
from __future__ import annotations
import re
from typing import Optional
from trace_core.models.common import TransformationType


_SETTER_RE = re.compile(r"report\.|output\.|result\.", re.IGNORECASE)
_OVERRIDE_RE = re.compile(r"override|overwrite|replace|forceSet", re.IGNORECASE)
_DEFAULT_RE = re.compile(r"default|fallback|orElse|getOrDefault|null\s*\?", re.IGNORECASE)
_ENRICH_RE = re.compile(r"enrich|augment|populate|fill|merge", re.IGNORECASE)
_EXTRACT_RE = re.compile(r"get|extract|fetch|read|load|parse", re.IGNORECASE)
_MAP_RE = re.compile(r"map|convert|transform|translate", re.IGNORECASE)


class TransformationClassifier:
    """Classifies a code snippet into a TransformationType."""

    def classify(
        self,
        method_name: str,
        body_snippet: Optional[str] = None,
        is_final_setter: bool = False,
    ) -> TransformationType:
        if is_final_setter or _SETTER_RE.search(method_name or ""):
            return TransformationType.FINAL_REPORT_ASSIGNMENT
        name = method_name or ""
        snippet = body_snippet or ""
        combined = f"{name} {snippet}"

        if _OVERRIDE_RE.search(combined):
            return TransformationType.OVERRIDE
        if _DEFAULT_RE.search(combined):
            return TransformationType.DEFAULTING
        if _ENRICH_RE.search(combined):
            return TransformationType.ENRICHMENT
        if _MAP_RE.search(combined):
            return TransformationType.MAPPING
        if _EXTRACT_RE.search(name):
            return TransformationType.EXTRACTION
        return TransformationType.PASS_THROUGH
