"""XSLT parser using lxml for namespace-aware extraction of templates and field mappings."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from orchestrator import live_events
from orchestrator.models import NodeMeta, XsltFinding

logger = logging.getLogger(__name__)

XSLT_NS = {"xsl": "http://www.w3.org/1999/XSL/Transform"}


class XsltParser:
    """Parses XSLT files to extract template definitions, value-of selects, and template calls."""

    def __init__(self, repo_name: str = "") -> None:
        self._repo_name = repo_name

    def parse_file(self, file_path: Path) -> list[XsltFinding]:
        logger.info("Parsing XSLT file: %s (repo=%s)", file_path, self._repo_name)
        live_events.emit(live_events.PARSE_START, {"file": str(file_path), "parser": "xslt", "repo": self._repo_name})
        tree = etree.parse(str(file_path))  # noqa: S320
        root = tree.getroot()
        findings: list[XsltFinding] = []

        templates = root.xpath("//xsl:template", namespaces=XSLT_NS)
        logger.debug("  Found %d template(s) in %s", len(templates), file_path.name)

        for template in templates:
            tpl_name = template.get("name", "")
            tpl_match = template.get("match", "")
            tpl_label = tpl_name or tpl_match or "(anonymous)"
            logger.debug("  Template: name='%s' match='%s'", tpl_name, tpl_match)

            # xsl:value-of — field extraction
            for value_of in template.xpath(".//xsl:value-of", namespaces=XSLT_NS):
                select = value_of.get("select", "")
                target_field = self._parent_element_name(value_of)
                field_name = self._extract_field_name(select)
                logger.debug("    value-of: select='%s' -> parent_element='%s' (field='%s')", select, target_field, field_name)

                findings.append(
                    XsltFinding(
                        template_name=tpl_label,
                        template_match=tpl_match,
                        field_source=select,
                        field_target=target_field,
                        finding_type="value_of",
                        meta=self._meta(file_path, value_of),
                        repo_name=self._repo_name,
                    )
                )

            # xsl:call-template — template invocation
            for call in template.xpath(
                ".//xsl:call-template", namespaces=XSLT_NS
            ):
                called_name = call.get("name", "")
                logger.debug("    call-template: '%s' -> '%s'", tpl_label, called_name)
                findings.append(
                    XsltFinding(
                        template_name=tpl_label,
                        template_match=tpl_match,
                        field_source=None,
                        field_target=called_name,
                        finding_type="template_call",
                        meta=self._meta(file_path, call),
                        repo_name=self._repo_name,
                    )
                )

            # xsl:copy-of — bulk field mapping
            for copy_of in template.xpath(".//xsl:copy-of", namespaces=XSLT_NS):
                select = copy_of.get("select", "")
                logger.debug("    copy-of: select='%s' -> parent='%s'", select, self._parent_element_name(copy_of))
                findings.append(
                    XsltFinding(
                        template_name=tpl_label,
                        template_match=tpl_match,
                        field_source=select,
                        field_target=self._parent_element_name(copy_of),
                        finding_type="field_mapping",
                        meta=self._meta(file_path, copy_of),
                        repo_name=self._repo_name,
                    )
                )

        logger.info("  Parsed %s: %d findings", file_path.name, len(findings))
        live_events.emit(live_events.PARSE_COMPLETE, {
            "file": str(file_path), "parser": "xslt",
            "findings": len(findings), "repo": self._repo_name,
        })
        return findings

    def parse_directory(self, dir_path: Path) -> list[XsltFinding]:
        logger.info("Parsing XSLT directory: %s", dir_path)
        findings: list[XsltFinding] = []
        xsl_files = sorted(dir_path.rglob("*.xsl"))
        xslt_files = sorted(dir_path.rglob("*.xslt"))
        logger.info("  Found %d .xsl + %d .xslt files in %s", len(xsl_files), len(xslt_files), dir_path)
        for xslt_file in xsl_files + xslt_files:
            findings.extend(self.parse_file(xslt_file))
        logger.info("  Total XSLT findings from %s: %d", dir_path, len(findings))
        return findings

    @staticmethod
    def _extract_field_name(xpath_expr: str) -> str | None:
        """Extract the terminal field name from an XPath expression.

        Examples:
            "order/customerName"  -> "customerName"
            "@id"                 -> "id"
            "ns:field[1]"        -> "field"
        """
        if not xpath_expr:
            return None
        # Take last path segment
        segment = xpath_expr.rsplit("/", 1)[-1]
        # Strip attribute prefix
        segment = segment.lstrip("@")
        # Strip namespace prefix
        if ":" in segment:
            segment = segment.split(":", 1)[1]
        # Strip predicates
        if "[" in segment:
            segment = segment.split("[", 1)[0]
        return segment.strip() or None

    @staticmethod
    def _parent_element_name(elem: etree._Element) -> str | None:
        """Get the local name of the parent non-XSL element."""
        parent = elem.getparent()
        while parent is not None:
            ns = parent.tag.split("}")[0].lstrip("{") if "}" in parent.tag else ""
            if ns != "http://www.w3.org/1999/XSL/Transform":
                local = parent.tag.split("}")[-1] if "}" in parent.tag else parent.tag
                return local
            parent = parent.getparent()
        return None

    @staticmethod
    def _meta(file_path: Path, elem: etree._Element) -> NodeMeta:
        snippet = etree.tostring(elem, encoding="unicode", pretty_print=True).strip()
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
        return NodeMeta(
            file_path=str(file_path),
            line_number=getattr(elem, "sourceline", 0) or 0,
            code_snippet=snippet,
        )
