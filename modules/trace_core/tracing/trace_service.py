"""TraceService – public entry point for field-level lineage tracing."""
from __future__ import annotations
import os
import uuid
import yaml
from typing import Optional, List, Dict, Any

from modules.trace_core.indexers.repo_indexer import RepoIndexer, Index
from modules.trace_core.tracing.trace_context import TraceContext
from modules.trace_core.tracing.field_trace_engine import FieldTraceEngine
from modules.trace_core.tracing.branch_trace_engine import BranchTraceEngine
from modules.trace_core.graph.nx_graph_builder import NxGraphBuilder
from modules.trace_core.exporters.trace_result import TraceResult
from modules.trace_core.explain.trace_summarizer import TraceSummarizer
from modules.trace_core.logging.context_logger import ContextLogger

_logger = ContextLogger("trace")


class TraceService:
    """Orchestrates the full lineage trace lifecycle."""

    def __init__(self, config_path: str = "configs/app.yaml"):
        self._config = self._load_config(config_path)
        self._trace_config = self._load_trace_config()
        self._index: Optional[Index] = None
        self._repo_indexer = RepoIndexer()
        self._summarizer = TraceSummarizer()
        self._graph_builder = NxGraphBuilder()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trace(
        self,
        field_name: str,
        jurisdiction: Optional[str] = None,
        package_filters: Optional[List[str]] = None,
        max_depth: int = 20,
        enable_condition_tracing: bool = True,
        enable_xslt_imports: bool = True,
    ) -> TraceResult:
        """Run a full field lineage trace and return a TraceResult."""
        trace_id = str(uuid.uuid4())
        logger = ContextLogger("trace", trace_id=trace_id, field_name=field_name)
        logger.info(f"Starting trace for field '{field_name}'", jurisdiction=jurisdiction)

        # Ensure index exists
        index = self._get_or_build_index(field_name)

        ctx = TraceContext(
            trace_id=trace_id,
            field_name=field_name,
            jurisdiction=jurisdiction,
            package_filters=package_filters or [],
            max_depth=max_depth,
            config=self._trace_config,
            enable_condition_tracing=enable_condition_tracing,
            enable_xslt_imports=enable_xslt_imports,
        )

        engine = FieldTraceEngine(index, self._trace_config)
        branch_engine = BranchTraceEngine()

        nodes, edges, origin = engine.trace(field_name, ctx)
        branches = branch_engine.build_branches(nodes, edges, ctx)

        graph = self._graph_builder.build(nodes, edges)
        summary = self._summarizer.summarize(field_name, origin, nodes, edges, branches)

        logger.info(
            f"Trace complete – {len(nodes)} nodes, {len(branches)} branches",
            trace_id=trace_id,
        )

        return TraceResult(
            field_name=field_name,
            trace_id=trace_id,
            summary=summary,
            graph=graph,
            nodes=nodes,
            edges=edges,
            branches=branches,
            metadata={"origin": origin.value, "jurisdiction": jurisdiction},
            evidence_list=[n.evidence for n in nodes],
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_build_index(self, field_name: str) -> Index:
        if self._index is not None:
            return self._index
        repo_paths = self._get_repo_paths()
        _logger.info(f"Building index for {len(repo_paths)} repositories")
        self._index = self._repo_indexer.index(repo_paths, field_name=field_name)
        return self._index

    def _get_repo_paths(self) -> List[str]:
        repos_cfg_path = self._config.get("repositories_file", "configs/repositories.yaml")
        try:
            with open(repos_cfg_path) as f:
                repos_cfg = yaml.safe_load(f)
            return [
                r["path"] for r in repos_cfg.get("repositories", [])
                if r.get("enabled", True)
            ]
        except Exception:
            pass
        # Fallback: return configured inline repos
        return self._config.get("repositories", [])

    def _load_config(self, path: str) -> Dict[str, Any]:
        if os.path.isfile(path):
            try:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as exc:
                _logger.warning(f"Cannot load config {path}: {exc}")
        return {}

    def _load_trace_config(self) -> Dict[str, Any]:
        trace_cfg_path = self._config.get("trace_rules_file", "configs/trace_rules.yaml")
        if os.path.isfile(trace_cfg_path):
            try:
                with open(trace_cfg_path) as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {
            "trace": {
                "includePackages": ["*nomura*", "*no*"],
                "excludePackages": ["java.*", "javax.*", "org.springframework.*"],
                "stopPackages": ["org.apache.*"],
                "maxDepth": 20,
                "followInternalCallsOnly": True,
                "enableConditionTracing": True,
                "enableXsltImports": True,
            }
        }
