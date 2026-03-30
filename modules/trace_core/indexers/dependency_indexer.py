"""Maven module dependency graph builder."""
from __future__ import annotations
from typing import List, Dict
from modules.trace_core.scanner.module_discovery import ModuleDiscovery, ModuleGraph
from modules.trace_core.logging.logger_factory import LoggerFactory

logger = LoggerFactory.get("scanner")


class DependencyIndexer:
    """Builds a Maven module dependency graph from repo roots."""

    def __init__(self):
        self._discovery = ModuleDiscovery()

    def build(self, repo_roots: List[str]) -> ModuleGraph:
        logger.info(f"Building dependency graph for {len(repo_roots)} repos")
        return self._discovery.discover(repo_roots)
