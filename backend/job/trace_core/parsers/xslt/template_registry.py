"""Registry of all XSLT templates across files."""
from __future__ import annotations
from typing import Dict, List, Optional
from trace_core.models.xslt_models import XsltTemplate


class TemplateRegistry:
    """Maintains an index of XsltTemplate objects by name and file."""

    def __init__(self):
        self._by_name: Dict[str, List[XsltTemplate]] = {}
        self._by_file: Dict[str, List[XsltTemplate]] = {}

    def register(self, template: XsltTemplate):
        self._by_name.setdefault(template.name, []).append(template)
        self._by_file.setdefault(template.file_path, []).append(template)

    def find(self, name: str) -> Optional[XsltTemplate]:
        """Return the first registered template with the given name."""
        hits = self._by_name.get(name, [])
        return hits[0] if hits else None

    def find_all(self, name: str) -> List[XsltTemplate]:
        return self._by_name.get(name, [])

    def get_file_templates(self, file_path: str) -> List[XsltTemplate]:
        return self._by_file.get(file_path, [])

    def all_templates(self) -> List[XsltTemplate]:
        return [t for templates in self._by_name.values() for t in templates]

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_name.values())
