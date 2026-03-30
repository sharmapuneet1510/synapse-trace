"""Extracts xsl:variable and xsl:param elements."""
from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import List, Optional
from modules.trace_core.models.xslt_models import XsltVariable, XsltParam

XSL_NS = "http://www.w3.org/1999/XSL/Transform"


def _tag(local: str) -> str:
    return f"{{{XSL_NS}}}{local}"


class VariableExtractor:
    """Extracts variables and params from an XSL element."""

    def extract_variables(self, el: ET.Element, line_offset: int = 0) -> List[XsltVariable]:
        result = []
        for child in el.iter(_tag("variable")):
            name = child.get("name", "")
            select = child.get("select")
            content = (child.text or "").strip() or None
            result.append(XsltVariable(name=name, select=select, content=content, line_number=line_offset))
        return result

    def extract_params(self, el: ET.Element, line_offset: int = 0) -> List[XsltParam]:
        result = []
        for child in el:
            if child.tag == _tag("param"):
                name = child.get("name", "")
                select = child.get("select")
                result.append(XsltParam(name=name, select=select, line_number=line_offset))
        return result
