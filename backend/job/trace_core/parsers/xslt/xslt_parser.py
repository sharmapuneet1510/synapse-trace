"""XSLT file parser using xml.etree.ElementTree."""
import os
import xml.etree.ElementTree as ET
from typing import Optional, List
from trace_core.models.xslt_models import (
    XsltFile, XsltTemplate, XsltCallTemplate, XsltApplyTemplates,
)
from trace_core.logging.logger_factory import LoggerFactory
from trace_core.utils.file_utils import read_file_safe
from .variable_extractor import VariableExtractor
from .condition_extractor import XsltConditionExtractor
from .output_mapping_extractor import OutputMappingExtractor

logger = LoggerFactory.get("parser")

XSL_NS = "http://www.w3.org/1999/XSL/Transform"
NS = {"xsl": XSL_NS}


def _tag(local: str) -> str:
    return f"{{{XSL_NS}}}{local}"


class XsltParser:
    """Parses XSLT files into XsltFile models."""

    def __init__(self):
        self._var_extractor = VariableExtractor()
        self._cond_extractor = XsltConditionExtractor()
        self._output_extractor = OutputMappingExtractor()

    def parse_file(
        self,
        path: str,
        repository: Optional[str] = None,
        module: Optional[str] = None,
    ) -> Optional[XsltFile]:
        """Parse an XSLT file and return an XsltFile model."""
        source = read_file_safe(path)
        if source is None:
            logger.warning(f"Cannot read XSLT file: {path}")
            return None

        try:
            root = ET.fromstring(source.encode("utf-8"))
        except ET.ParseError as exc:
            logger.error(f"XML parse error in {path}: {exc}")
            return None

        xslt_file = XsltFile(file_path=path, repository=repository, module=module)

        # Global variables and params
        xslt_file.global_variables = self._var_extractor.extract_variables(root)
        xslt_file.global_params = self._var_extractor.extract_params(root)

        # Imports and includes
        for imp in root.findall(_tag("import")):
            href = imp.get("href")
            if href:
                xslt_file.imports.append(href)
        for inc in root.findall(_tag("include")):
            href = inc.get("href")
            if href:
                xslt_file.includes.append(href)

        # Templates
        for tmpl_el in root.findall(_tag("template")):
            tmpl = self._parse_template(tmpl_el, path, repository, module)
            if tmpl:
                xslt_file.templates.append(tmpl)

        logger.debug(
            f"Parsed XSLT: {path} ({len(xslt_file.templates)} templates, "
            f"{len(xslt_file.imports)} imports)",
            extra={"repository": repository},
        )
        return xslt_file

    def _parse_template(
        self,
        el: ET.Element,
        file_path: str,
        repository: Optional[str],
        module: Optional[str],
    ) -> Optional[XsltTemplate]:
        name = el.get("name", "")
        match = el.get("match")
        if not name and not match:
            return None

        tmpl = XsltTemplate(
            name=name or f"match:{match}",
            file_path=file_path,
            repository=repository,
            module=module,
            match=match,
        )

        tmpl.variables = self._var_extractor.extract_variables(el)
        tmpl.params = self._var_extractor.extract_params(el)
        tmpl.conditions = self._cond_extractor.extract(el)
        tmpl.output_mappings = self._output_extractor.extract(el)

        # call-template references
        for ct in el.iter(_tag("call-template")):
            ct_name = ct.get("name", "")
            params = {}
            for wp in ct.findall(_tag("with-param")):
                pname = wp.get("name", "")
                pval = wp.get("select", (wp.text or "").strip())
                params[pname] = pval
            tmpl.call_templates.append(XsltCallTemplate(name=ct_name, params=params))

        # apply-templates references
        for at in el.iter(_tag("apply-templates")):
            select = at.get("select")
            mode = at.get("mode")
            tmpl.apply_templates.append(XsltApplyTemplates(select=select, mode=mode))

        # Capture raw XML
        tmpl.raw_xml = ET.tostring(el, encoding="unicode")
        return tmpl
