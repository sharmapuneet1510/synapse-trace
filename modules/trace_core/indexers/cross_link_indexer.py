"""Cross-links XSLT output field names to Java DTO setter methods."""
from __future__ import annotations
import re
from typing import Dict, List, TYPE_CHECKING
from modules.trace_core.models.java_models import JavaClass
from modules.trace_core.parsers.xslt.template_registry import TemplateRegistry
from modules.trace_core.logging.logger_factory import LoggerFactory

logger = LoggerFactory.get("scanner")

SETTER_RE = re.compile(r"set([A-Z]\w*)")


def _setter_to_field(setter_name: str) -> str:
    """Convert setClearedFlag → CLEARED_FLAG style."""
    name = re.sub(r"([A-Z])", r"_\1", setter_name).upper().lstrip("_")
    return name


class CrossLinkIndexer:
    """Links XSLT output field names to Java setter methods."""

    def build_links(
        self,
        java_index: Dict[str, JavaClass],
        xslt_registry: TemplateRegistry,
    ) -> Dict[str, List[str]]:
        """Return a mapping of field_name → list of Java method FQNs that set it."""
        links: Dict[str, List[str]] = {}

        # Collect all setters from Java
        setter_map: Dict[str, List[str]] = {}  # field_name_key → [method_fqn]
        for fqn, cls in java_index.items():
            for method in cls.methods:
                m = SETTER_RE.match(method.name)
                if m:
                    field_key = _setter_to_field(m.group(1))
                    setter_map.setdefault(field_key, []).append(f"{fqn}.{method.name}")

        # For each XSLT output mapping, find matching Java setters
        for tmpl in xslt_registry.all_templates():
            for om in tmpl.output_mappings:
                field_key = om.field_name.upper().replace("-", "_")
                if field_key in setter_map:
                    links.setdefault(field_key, []).extend(setter_map[field_key])

        logger.info(f"Cross-link index built: {len(links)} field links")
        return links
