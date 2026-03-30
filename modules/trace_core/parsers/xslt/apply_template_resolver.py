"""Resolves xsl:apply-templates to matching templates."""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from modules.trace_core.models.xslt_models import XsltTemplate

if TYPE_CHECKING:
    from .template_registry import TemplateRegistry


class ApplyTemplateResolver:
    """Finds templates matching an apply-templates select expression."""

    def __init__(self, registry: "TemplateRegistry"):
        self._registry = registry

    def resolve(self, select: Optional[str], mode: Optional[str] = None) -> List[XsltTemplate]:
        """Return templates that could match the apply-templates select."""
        candidates = []
        for t in self._registry.all_templates():
            if mode and t.match == mode:
                candidates.append(t)
            elif select and t.match and select in t.match:
                candidates.append(t)
        return candidates
