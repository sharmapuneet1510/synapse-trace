"""Orchestrates scanning and indexing of all repositories."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from modules.trace_core.scanner.repo_scanner import RepoScanner, RepoInfo
from modules.trace_core.scanner.file_registry import FileRegistry
from modules.trace_core.models.java_models import JavaClass
from modules.trace_core.parsers.xslt.template_registry import TemplateRegistry
from modules.trace_core.logging.logger_factory import LoggerFactory
from modules.trace_core.utils.timer import Timer
from .java_indexer import JavaIndexer
from .xslt_indexer import XsltIndexer
from .cross_link_indexer import CrossLinkIndexer

logger = LoggerFactory.get("scanner")


@dataclass
class Index:
    java_classes: Dict[str, JavaClass] = field(default_factory=dict)
    xslt_templates: TemplateRegistry = field(default_factory=TemplateRegistry)
    file_registry: FileRegistry = field(default_factory=FileRegistry)
    cross_links: Dict[str, List[str]] = field(default_factory=dict)
    repos: List[RepoInfo] = field(default_factory=list)


class RepoIndexer:
    """Orchestrates full repo scanning and indexing."""

    def __init__(self):
        self._scanner = RepoScanner()
        self._java_indexer = JavaIndexer()
        self._xslt_indexer = XsltIndexer()
        self._cross_linker = CrossLinkIndexer()
        self._file_registry = FileRegistry()

    def index(self, repo_paths: List[str], field_name: Optional[str] = None) -> Index:
        logger.info(f"Starting full index for {len(repo_paths)} repositories")
        idx = Index()

        with Timer("full repository index", logger=logger):
            repos = self._scanner.scan(repo_paths)
            idx.repos = repos

            all_java: List[str] = []
            all_xslt: List[str] = []

            for repo in repos:
                for f in repo.java_files:
                    self._file_registry.register_file(f, "java", repository=repo.name)
                for f in repo.xslt_files:
                    self._file_registry.register_file(f, "xslt", repository=repo.name)
                all_java.extend(repo.java_files)
                all_xslt.extend(repo.xslt_files)

            idx.file_registry = self._file_registry
            idx.java_classes = self._java_indexer.index(all_java, field_name=field_name)
            idx.xslt_templates = self._xslt_indexer.index(all_xslt)
            idx.cross_links = self._cross_linker.build_links(idx.java_classes, idx.xslt_templates)

        logger.info(
            f"Index complete: {len(idx.java_classes)} Java classes, "
            f"{len(idx.xslt_templates)} XSLT templates, "
            f"{len(idx.cross_links)} cross-links"
        )
        return idx
