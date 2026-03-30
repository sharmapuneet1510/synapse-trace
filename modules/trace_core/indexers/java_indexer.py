"""Java source indexer – parses all .java files into a class registry."""
from __future__ import annotations
from typing import List, Dict, Optional
from modules.trace_core.models.java_models import JavaClass
from modules.trace_core.parsers.java.java_parser import JavaParser
from modules.trace_core.logging.logger_factory import LoggerFactory
from modules.trace_core.utils.timer import Timer

logger = LoggerFactory.get("scanner")


class JavaIndexer:
    """Parses all Java files and builds a FQN → JavaClass registry."""

    def __init__(self):
        self._parser = JavaParser()

    def index(
        self,
        java_files: List[str],
        repository: Optional[str] = None,
        module: Optional[str] = None,
        field_name: Optional[str] = None,
    ) -> Dict[str, JavaClass]:
        """Return a dict of fqn → JavaClass for all parseable Java files."""
        registry: Dict[str, JavaClass] = {}
        with Timer("Java indexing", logger=logger):
            for path in java_files:
                try:
                    cls = self._parser.parse_file(path, repository=repository, module=module, field_name=field_name)
                    if cls:
                        registry[cls.fqn] = cls
                except Exception as exc:
                    logger.error(f"Failed to index Java file {path}: {exc}", exc_info=True)
        logger.info(f"Java indexing complete: {len(registry)} classes indexed", extra={"repository": repository})
        return registry
