"""Orchestrates scanning and indexing of all repositories."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from trace_core.scanner.repo_scanner import RepoScanner, RepoInfo
from trace_core.scanner.file_registry import FileRegistry
from trace_core.models.java_models import JavaClass
from trace_core.parsers.xslt.template_registry import TemplateRegistry
from trace_core.logging.logger_factory import LoggerFactory
from trace_core.utils.timer import Timer
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
        """Scan and index all repository root directories.

        Parameters
        ----------
        repo_paths : List[str]
            Root directories of Maven projects (single-module or multi-module).
            Each path is walked recursively; all Java and XSLT files anywhere
            under it are indexed.  pom.xml files are parsed to extract Maven
            coordinates and sub-module membership.
        field_name : str, optional
            When provided, the Java indexer uses this as a hint to prioritise
            classes that reference the field.
        """
        logger.info(f"Starting full index for {len(repo_paths)} repositories")
        idx = Index()

        with Timer("full repository index", logger=logger):
            repos = self._scanner.scan(repo_paths)
            idx.repos = repos

            all_java: List[str] = []
            all_xslt: List[str] = []

            for repo in repos:
                # Register every file with its repository name AND Maven
                # sub-module (populated for multi-module projects).
                for f in repo.java_files:
                    module = repo.file_module_map.get(f)
                    self._file_registry.register_file(
                        f, "java", repository=repo.name, module=module
                    )
                for f in repo.xslt_files:
                    module = repo.file_module_map.get(f)
                    self._file_registry.register_file(
                        f, "xslt", repository=repo.name, module=module
                    )
                all_java.extend(repo.java_files)
                all_xslt.extend(repo.xslt_files)

            idx.file_registry = self._file_registry
            idx.java_classes  = self._java_indexer.index(all_java, field_name=field_name)
            idx.xslt_templates = self._xslt_indexer.index(all_xslt)
            idx.cross_links    = self._cross_linker.build_links(
                idx.java_classes, idx.xslt_templates
            )

        logger.info(
            f"Index complete: "
            f"{sum(1 for r in repos if r.is_multi_module)} multi-module repos | "
            f"{len(idx.java_classes)} Java classes | "
            f"{len(idx.xslt_templates)} XSLT templates | "
            f"{len(idx.cross_links)} cross-links"
        )
        return idx
