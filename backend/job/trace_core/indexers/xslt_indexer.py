"""XSLT source indexer – parses all XSLT files into a template registry."""
from __future__ import annotations
from typing import List, Optional
from trace_core.parsers.xslt.xslt_parser import XsltParser
from trace_core.parsers.xslt.template_registry import TemplateRegistry
from trace_core.parsers.xslt.import_resolver import ImportResolver
from trace_core.models.xslt_models import XsltFile
from trace_core.logging.logger_factory import LoggerFactory
from trace_core.utils.timer import Timer

logger = LoggerFactory.get("scanner")


class XsltIndexer:
    """Parses all XSLT files and builds a TemplateRegistry."""

    def __init__(self):
        self._parser = XsltParser()
        self._resolver = ImportResolver()
        self._visited: set = set()

    def index(
        self,
        xslt_files: List[str],
        repository: Optional[str] = None,
        module: Optional[str] = None,
        follow_imports: bool = True,
    ) -> TemplateRegistry:
        registry = TemplateRegistry()
        parsed_files: List[XsltFile] = []

        with Timer("XSLT indexing", logger=logger):
            queue = list(xslt_files)
            while queue:
                path = queue.pop(0)
                if path in self._visited:
                    continue
                self._visited.add(path)
                try:
                    xslt_file = self._parser.parse_file(path, repository=repository, module=module)
                    if not xslt_file:
                        continue
                    parsed_files.append(xslt_file)
                    for tmpl in xslt_file.templates:
                        registry.register(tmpl)

                    if follow_imports:
                        for href in xslt_file.imports + xslt_file.includes:
                            resolved = self._resolver.resolve(href, path)
                            if resolved and resolved not in self._visited:
                                queue.append(resolved)
                except Exception as exc:
                    logger.error(f"Failed to index XSLT file {path}: {exc}", exc_info=True)

        logger.info(f"XSLT indexing complete: {len(registry)} templates", extra={"repository": repository})
        return registry
