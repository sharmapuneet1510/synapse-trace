"""Resolves xsl:call-template references via TemplateRegistry."""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from trace_core.models.xslt_models import XsltTemplate

if TYPE_CHECKING:
    from .template_registry import TemplateRegistry


class CallTemplateResolver:
    """Resolves call-template names to XsltTemplate objects."""

    def __init__(self, registry: "TemplateRegistry"):
        self._registry = registry

    def resolve(self, name: str) -> Optional[XsltTemplate]:
        """Return the template for the given name, or None."""
        return self._registry.find(name)
