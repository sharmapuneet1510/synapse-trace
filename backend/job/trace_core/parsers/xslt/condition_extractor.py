"""Extracts xsl:if and xsl:choose/xsl:when conditions."""
from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import List
from trace_core.models.xslt_models import XsltCondition

XSL_NS = "http://www.w3.org/1999/XSL/Transform"


def _tag(local: str) -> str:
    return f"{{{XSL_NS}}}{local}"


class XsltConditionExtractor:
    """Extracts conditional structures from an XSL template element."""

    def extract(self, el: ET.Element, line_offset: int = 0) -> List[XsltCondition]:
        conditions = []
        for child in el.iter():
            if child.tag == _tag("if"):
                test = child.get("test", "")
                conditions.append(XsltCondition(test=test, type="xsl:if", line_number=line_offset))
            elif child.tag == _tag("when"):
                test = child.get("test", "")
                conditions.append(XsltCondition(test=test, type="xsl:when", line_number=line_offset))
        return conditions
