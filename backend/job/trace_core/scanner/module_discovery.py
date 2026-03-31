"""Maven module dependency discovery."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .maven_scanner import MavenScanner, MavenModule
from trace_core.logging.logger_factory import LoggerFactory

logger = LoggerFactory.get("scanner")


@dataclass
class ModuleGraph:
    modules: Dict[str, MavenModule] = field(default_factory=dict)  # artifact_id -> MavenModule
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # artifact_id -> [artifact_id]


class ModuleDiscovery:
    """Recursively discovers Maven modules and builds a dependency graph."""

    def __init__(self):
        self._scanner = MavenScanner()

    def discover(self, repo_roots: List[str]) -> ModuleGraph:
        """Discover all Maven modules under the given repository roots."""
        graph = ModuleGraph()
        pom_paths = self._find_all_poms(repo_roots)
        logger.info(f"Discovered {len(pom_paths)} pom.xml files")

        for pom in pom_paths:
            mod = self._scanner.scan_pom(pom)
            if mod and mod.artifact_id:
                graph.modules[mod.artifact_id] = mod

        for art_id, mod in graph.modules.items():
            deps = [d.artifact_id for d in mod.dependencies if d.artifact_id in graph.modules]
            graph.dependencies[art_id] = deps

        logger.info(f"Module graph built: {len(graph.modules)} modules")
        return graph

    def _find_all_poms(self, roots: List[str]) -> List[str]:
        poms = []
        for root in roots:
            for dirpath, _, filenames in os.walk(root):
                for f in filenames:
                    if f == "pom.xml":
                        poms.append(os.path.join(dirpath, f))
        return poms
