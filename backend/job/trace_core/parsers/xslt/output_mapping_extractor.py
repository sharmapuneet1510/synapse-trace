"""Extracts field output mappings from XSLT templates."""
from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from typing import List
from trace_core.models.xslt_models import XsltOutputMapping

XSL_NS = "http://www.w3.org/1999/XSL/Transform"
FIELD_LIKE_RE = re.compile(r"[A-Z_]{3,}", re.IGNORECASE)


def _tag(local: str) -> str:
    return f"{{{XSL_NS}}}{local}"


class OutputMappingExtractor:
    """Identifies field output mappings in XSLT templates."""

    def extract(self, el: ET.Element, line_offset: int = 0) -> List[XsltOutputMapping]:
        mappings = []
        # Look for value-of elements with select containing field-like names
        for child in el.iter(_tag("value-of")):
            select = child.get("select", "")
            if select:
                # Check parent for field name hints
                field_name = self._infer_field_name(el, select)
                if field_name:
                    mappings.append(XsltOutputMapping(
                        field_name=field_name,
                        xpath_expression=select,
                        line_number=line_offset,
                    ))
        # Also check attribute value templates
        for child in el.iter():
            for attr_name, attr_val in child.attrib.items():
                if "{" in attr_val and "}" in attr_val:
                    field_name = self._infer_field_name(el, attr_name)
                    if field_name:
                        xpath = re.search(r"\{([^}]+)\}", attr_val)
                        if xpath:
                            mappings.append(XsltOutputMapping(
                                field_name=field_name,
                                xpath_expression=xpath.group(1),
                                line_number=line_offset,
                            ))
        return mappings

    def _infer_field_name(self, context: ET.Element, hint: str) -> str:
        """Try to infer field name from context element name or hint."""
        context_tag = re.sub(r"\{[^}]+\}", "", context.get("name", "") or context.tag or "")
        if context_tag and FIELD_LIKE_RE.search(context_tag):
            return context_tag
        if hint and FIELD_LIKE_RE.search(hint):
            m = FIELD_LIKE_RE.search(hint)
            return m.group(0) if m else ""
        return ""
