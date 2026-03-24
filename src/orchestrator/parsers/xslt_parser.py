"""XSLT parser using lxml for namespace-aware extraction of templates and field mappings."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from orchestrator.models import NodeMeta, XsltFinding

XSLT_NS = {"xsl": "http://www.w3.org/1999/XSL/Transform"}


class XsltParser:
    """Parses XSLT files to extract template definitions, value-of selects, and template calls."""

    def __init__(self, repo_name: str = "") -> None:
        self._repo_name = repo_name

    def parse_file(self, file_path: Path) -> list[XsltFinding]:
        tree = etree.parse(str(file_path))  # noqa: S320
        root = tree.getroot()
        findings: list[XsltFinding] = []

        for template in root.xpath("//xsl:template", namespaces=XSLT_NS):
            tpl_name = template.get("name", "")
            tpl_match = template.get("match", "")
            tpl_label = tpl_name or tpl_match or "(anonymous)"

            # xsl:value-of — field extraction
            for value_of in template.xpath(".//xsl:value-of", namespaces=XSLT_NS):
                select = value_of.get("select", "")
                target_field = self._parent_element_name(value_of)
                field_name = self._extract_field_name(select)

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

        return findings

    def parse_directory(self, dir_path: Path) -> list[XsltFinding]:
        findings: list[XsltFinding] = []
        for xslt_file in sorted(dir_path.rglob("*.xsl")):
            findings.extend(self.parse_file(xslt_file))
        for xslt_file in sorted(dir_path.rglob("*.xslt")):
            findings.extend(self.parse_file(xslt_file))
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
