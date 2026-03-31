"""
Data Lineage Orchestrator  –  public entry point.

Repository layout
-----------------
``lib_repos`` and ``project_repos`` each accept a **list of root directories
of Maven projects** — single-module or multi-module.  You pass the top-level
project directory; the scanner recursively discovers all Java (``.java``) and
XSLT (``.xsl`` / ``.xslt``) source files underneath it, regardless of nesting
depth.

A typical multi-module Maven project is structured like this::

    trade-service/                         ← pass this root path
    ├── pom.xml                            ← parent POM (lists sub-modules)
    ├── xslt-module/
    │   ├── pom.xml
    │   └── src/main/resources/xslt/
    │       └── mapTrade.xslt              ← discovered automatically
    ├── service-module/
    │   ├── pom.xml
    │   └── src/main/java/com/corp/svc/
    │       └── TradeService.java          ← discovered automatically
    └── model-module/
        ├── pom.xml
        └── src/main/java/com/corp/model/
            └── Trade.java                 ← discovered automatically

``lib_repos``     – shared library / utility projects (indexed but not used as
                    trace entry points; provide reusable class definitions
                    referenced by the project code).
``project_repos`` – main application projects where field traces begin.

Both accept single-module and multi-module Maven project roots interchangeably.
You do **not** need to enumerate individual modules — just provide the parent
directory and everything underneath it is picked up automatically.

Typical usage
-------------
    from src.orchestrator.data_lineage import scanner

    # Root directories of Maven projects — single-module or multi-module.
    lib_repos          = ["/repos/trade-lib"]      # shared utils / models
    project_repos      = ["/repos/trade-service"]  # main application project
    deep_scan_packages = ["com.corp.*"]
    fields             = ["N_CLEARED", "N_SETTLEMENT_DATE"]

    project = scanner.load_project(
        lib_repos=lib_repos,
        project_repos=project_repos,
        deep_scan_packages=deep_scan_packages,
    )

    for field in fields:
        trace = project.scan(
            key=field,                          # primary key — all output filenames
            field=field,
            deep_scan_packages=deep_scan_packages,
        )
        graph = trace.to_graph()
        graph.to_html()                         # → outputs/html/N_CLEARED.html
        graph.to_md()                           # → outputs/md/N_CLEARED.md
        graph.to_json()                         # → outputs/json/N_CLEARED.json

    # Merging two field graphs into one combined report
    trace_a = project.scan(key="N_CLEARED",         field="N_CLEARED")
    trace_b = project.scan(key="N_SETTLEMENT_DATE",  field="N_SETTLEMENT_DATE")
    graph_a  = trace_a.to_graph()
    graph_b  = trace_b.to_graph()
    graph_a.extend(graph=graph_b)               # merges in-place; key stays N_CLEARED
    graph_a.to_html()                           # combined report → N_CLEARED.html
"""
from __future__ import annotations

import json
import os
import uuid
from typing import List, Optional, Dict, Any

# ── core modules ─────────────────────────────────────────────────────────────
import sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from modules.trace_core.indexers.repo_indexer import RepoIndexer, Index
from modules.trace_core.tracing.trace_context import TraceContext
from modules.trace_core.tracing.field_trace_engine import FieldTraceEngine
from modules.trace_core.tracing.branch_trace_engine import BranchTraceEngine
from modules.trace_core.graph.nx_graph_builder import NxGraphBuilder
from modules.trace_core.exporters.trace_result import TraceResult
from modules.trace_core.exporters.html_exporter import HtmlExporter
from modules.trace_core.explain.trace_summarizer import TraceSummarizer
from modules.trace_core.logging.context_logger import ContextLogger

_logger = ContextLogger("data_lineage")

# ── output directories ────────────────────────────────────────────────────────
_OUT_HTML = os.path.join(_ROOT, "outputs", "html")
_OUT_MD   = os.path.join(_ROOT, "outputs", "md")
_OUT_JSON = os.path.join(_ROOT, "outputs", "json")


# ─────────────────────────────────────────────────────────────────────────────
# Graph  –  wrapper returned by Trace.to_graph()
# ─────────────────────────────────────────────────────────────────────────────

class Graph:
    """
    Thin wrapper around a completed TraceResult.

    Key
    ---
    Every Graph has a *key* — the primary identifier used for all output
    filenames (html / md / json).  By default the key equals the field name,
    but it can be overridden via ``project.scan(key=...)``.

    File exports  (each returns the saved file path):
        graph.to_html()   →  <output_dir>/<KEY>.html
        graph.to_md()     →  <output_dir>/<KEY>.md
        graph.to_json()   →  <output_dir>/<KEY>.json

    Graph composition:
        graph.extend(graph=another_graph)
            Merges nodes, edges, branches and the underlying NetworkX graph
            from *another_graph* into this one.  The primary key (and all
            output filenames) stays that of the receiver.  Returns ``self``
            so calls can be chained.

    LLM analysis (stub — wire llm_service._call_llm for real responses):
        graph.to_buissness_derivation()   plain-English field derivation
        graph.to_reporting_logic()        how the field drives report inclusion
        graph.to_enrichment_logic()       enrichment / override chain
        graph.to_downstream()             downstream impact analysis
        graph.to_example()                worked trade scenarios per branch
        graph.to_operation()              production runbook

    Every LLM method accepts two mutually exclusive prompt sources:
        prompt_name    (str) — name of a registered Jinja2 template  (default)
        custom_prompt  (str) — raw Jinja2 template string rendered with graph context

    All templates have access to these Jinja2 context variables:
        {{ field_name }}, {{ origin }}, {{ total_nodes }}, {{ branch_count }},
        {{ has_xslt }}, {{ has_java }}, {{ pipeline_steps }},
        {{ nodes }}   (list of dicts: label, transformation_type, class_or_template,
                       method, file, line, condition)
        {{ branches }} (list of dicts: branch_id, condition, outcome)
        {{ downstream_name }}, {{ downstream_packages }}, {{ metadata }}

    Custom prompt example:
        text = graph.to_buissness_derivation(
            custom_prompt=(
                "Field {{ field_name }} has {{ branch_count }} branches.\\n"
                "{% for b in branches %}  • {{ b.condition }} → {{ b.outcome }}\\n"
                "{% endfor %}"
                "Summarise the derivation logic in one paragraph."
            )
        )
    """

    def __init__(self, result: TraceResult, key: Optional[str] = None):
        self._result = result
        # The key drives output filenames; defaults to the traced field name.
        self._key = (key or result.field_name).upper()

    # ── Key ───────────────────────────────────────────────────────────────────

    @property
    def key(self) -> str:
        """Primary output key (used for all file names)."""
        return self._key

    # ── File exports ──────────────────────────────────────────────────────────

    def to_html(self, output_dir: Optional[str] = None) -> str:
        """Save a self-contained HTML report to <output_dir>/<KEY>.html.

        Returns the absolute path of the written file.
        """
        out_dir = output_dir or _OUT_HTML
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{self._key}.html")
        html = HtmlExporter().export(
            self._result.summary, self._result.nodes, self._result.branches,
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        _logger.info(f"HTML report saved: {path}")
        return path

    def to_md(self, output_dir: Optional[str] = None) -> str:
        """Save a Markdown lineage report to <output_dir>/<KEY>.md.

        Returns the absolute path of the written file.
        """
        out_dir = output_dir or _OUT_MD
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{self._key}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(_MdExporter().export(self._result))
        _logger.info(f"Markdown report saved: {path}")
        return path

    def to_json(self, output_dir: Optional[str] = None) -> str:
        """Save the full trace as JSON to <output_dir>/<KEY>.json.

        Serialises the complete TraceResult (nodes, edges, branches, graph,
        summary, metadata) and writes it to disk.

        Returns the absolute path of the written file.
        """
        out_dir = output_dir or _OUT_JSON
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{self._key}.json")
        payload = self._result.to_json()
        # Stamp the key into the exported payload so consumers know which
        # primary key produced this file.
        payload["key"] = self._key
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        _logger.info(f"JSON export saved: {path}")
        return path

    # ── Graph composition ─────────────────────────────────────────────────────

    def extend(self, graph: "Graph") -> "Graph":
        """Merge *graph* into this Graph in-place and return ``self``.

        What is merged
        --------------
        * Nodes   — deduplicated by ``node_id``
        * Edges   — deduplicated by ``(source_id, target_id, relation)``
        * Branches — deduplicated by ``branch_id``
        * NetworkX graph — composed via ``nx.compose`` (union of all nodes/edges)
        * Summary counts — recomputed from the merged node / branch lists
        * Metadata — ``merged_fields`` list updated; other keys preserved

        The receiver's *key* is unchanged; the incoming graph's field is
        appended to ``metadata["merged_fields"]`` for traceability.

        Parameters
        ----------
        graph : Graph
            Another Graph whose trace data will be folded into this one.

        Returns
        -------
        Graph
            ``self``, allowing chained calls::

                base.extend(graph=other_a).extend(graph=other_b)
        """
        import networkx as nx

        src = graph._result
        dst = self._result

        _logger.info(
            f"extend: merging '{src.field_name}' into key='{self._key}' "
            f"(+{len(src.nodes)} nodes, +{len(src.branches)} branches)"
        )

        # ── Merge nodes (deduplicate by node_id) ──────────────────────────────
        existing_node_ids = {n.node_id for n in dst.nodes}
        new_nodes = [n for n in src.nodes if n.node_id not in existing_node_ids]
        dst.nodes = dst.nodes + new_nodes

        # ── Merge edges (deduplicate by source/target/relation) ───────────────
        existing_edge_keys = {
            (e.source_id, e.target_id, e.relation) for e in dst.edges
        }
        new_edges = [
            e for e in src.edges
            if (e.source_id, e.target_id, e.relation) not in existing_edge_keys
        ]
        dst.edges = dst.edges + new_edges

        # ── Merge branches (deduplicate by branch_id) ─────────────────────────
        existing_branch_ids = {b.branch_id for b in dst.branches}
        new_branches = [b for b in src.branches if b.branch_id not in existing_branch_ids]
        dst.branches = dst.branches + new_branches

        # ── Merge evidence list ───────────────────────────────────────────────
        dst.evidence_list = dst.evidence_list + src.evidence_list

        # ── Compose NetworkX graphs ───────────────────────────────────────────
        dst.graph = nx.compose(dst.graph, src.graph)

        # ── Recompute summary counts ──────────────────────────────────────────
        dst.summary.total_nodes  = len(dst.nodes)
        dst.summary.branch_count = len(dst.branches)

        # ── Update metadata traceability ──────────────────────────────────────
        merged = dst.metadata.setdefault("merged_fields", [])
        if src.field_name not in merged:
            merged.append(src.field_name)

        _logger.info(
            f"extend: key='{self._key}' now has "
            f"{len(dst.nodes)} nodes, {len(dst.branches)} branches"
        )
        return self

    # ── LLM analysis methods ──────────────────────────────────────────────────

    def to_buissness_derivation(
        self,
        prompt_name: str = "business_derivation",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Plain-English explanation of how this field is derived.

        Parameters
        ----------
        prompt_name   : Named Jinja2 template (default 'business_derivation').
                        Available: business_derivation | technical_summary |
                        reporting_logic | enrichment_logic | downstream_impact |
                        examples | operations | field_impact | chat_context
        custom_prompt : Raw Jinja2 template string. When given, prompt_name is
                        ignored. Same context variables available as in named templates.

        Returns
        -------
        str — LLM response (stub returns placeholder until _call_llm is wired).
        """
        return self._run_prompt(
            prompt_name, default_fallback="business_derivation",
            custom_prompt=custom_prompt,
        )

    def to_reporting_logic(
        self,
        prompt_name: str = "reporting_logic",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """How this field drives trade report inclusion / categorisation.

        Parameters
        ----------
        prompt_name   : Named template (default 'reporting_logic').
        custom_prompt : Ad-hoc Jinja2 string override.
        """
        return self._run_prompt(
            prompt_name, default_fallback="reporting_logic",
            custom_prompt=custom_prompt,
        )

    def to_enrichment_logic(
        self,
        prompt_name: str = "enrichment_logic",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Extraction → enrichment → override chain for this field.

        Parameters
        ----------
        prompt_name   : Named template (default 'enrichment_logic').
        custom_prompt : Ad-hoc Jinja2 string override.
        """
        return self._run_prompt(
            prompt_name, default_fallback="enrichment_logic",
            custom_prompt=custom_prompt,
        )

    def to_downstream(
        self,
        downstream_name: Optional[str] = None,
        downstream_packages: Optional[List[str]] = None,
        prompt_name: str = "downstream_impact",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Downstream impact — which fields, reports and systems depend on this field.

        Parameters
        ----------
        downstream_name     : Specific downstream target to focus on.
        downstream_packages : Java packages owning downstream consumers.
        prompt_name         : Named template (default 'downstream_impact').
        custom_prompt       : Ad-hoc Jinja2 string override.
                              {{ downstream_name }} and {{ downstream_packages }}
                              are available as context variables.
        """
        self._result.metadata["downstream_name"]     = downstream_name
        self._result.metadata["downstream_packages"] = downstream_packages or []
        return self._run_prompt(
            prompt_name, default_fallback="downstream_impact",
            custom_prompt=custom_prompt,
        )

    def to_example(
        self,
        prompt_name: str = "examples",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Worked trade scenarios exercising every conditional branch.

        Parameters
        ----------
        prompt_name   : Named template (default 'examples').
        custom_prompt : Ad-hoc Jinja2 string override.
        """
        return self._run_prompt(
            prompt_name, default_fallback="examples",
            custom_prompt=custom_prompt,
        )

    def to_operation(
        self,
        prompt_name: str = "operations",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Production runbook: happy path, fallbacks, overrides, monitoring.

        Parameters
        ----------
        prompt_name   : Named template (default 'operations').
        custom_prompt : Ad-hoc Jinja2 string override.
        """
        return self._run_prompt(
            prompt_name, default_fallback="operations",
            custom_prompt=custom_prompt,
        )

    # ── Shared LLM runner ─────────────────────────────────────────────────────

    def _run_prompt(
        self,
        prompt_name: str,
        default_fallback: str,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Render a prompt and pass it to the LLM stub.

        Rendering priority
        ------------------
        1. custom_prompt  — rendered as a Jinja2 string with graph context
        2. prompt_name    — looked up in the registry (Jinja2 template)
        3. default_fallback — used when prompt_name is not registered

        LLM integration
        ---------------
        The rendered prompt is passed to llm_service._call_llm(prompt).
        Replace that method in src/api/services/llm_service.py to wire a
        real LLM (OpenAI / Claude / Bedrock / etc.).
        """
        import asyncio

        try:
            from src.api.prompts import prompt_registry, jinja_engine
            from src.api.services.llm_service import llm_service
        except ImportError as exc:
            _logger.warning(f"_run_prompt: modules not available ({exc})")
            return (
                f"[Stub — modules not loaded] "
                f"field={self._result.field_name} prompt={prompt_name}"
            )

        # ── Render the prompt ──────────────────────────────────────────────
        if custom_prompt is not None:
            # Ad-hoc Jinja2 string supplied by caller
            _logger.info(
                f"_run_prompt: field='{self._result.field_name}' "
                f"using custom_prompt (len={len(custom_prompt)})"
            )
            try:
                rendered = prompt_registry.render_custom(custom_prompt, self._result)
            except Exception as exc:
                _logger.warning(f"_run_prompt: custom_prompt render failed: {exc}")
                rendered = custom_prompt  # fall back to raw string
        else:
            # Named template
            resolved = (
                prompt_name
                if prompt_name in prompt_registry
                else default_fallback
            )
            if resolved not in prompt_registry:
                _logger.warning(
                    f"_run_prompt: prompt '{resolved}' not registered"
                )
                return (
                    f"[Stub] Prompt '{resolved}' not registered. "
                    f"Available: {prompt_registry.list_prompts()}"
                )
            _logger.info(
                f"_run_prompt: field='{self._result.field_name}' prompt='{resolved}'"
            )
            rendered = prompt_registry.render(resolved, self._result)

        # ── Call LLM stub ──────────────────────────────────────────────────
        context = {
            "field_name": self._result.field_name,
            "trace_id":   self._result.trace_id,
        }
        try:
            asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    asyncio.run,
                    llm_service._call_llm(rendered, context=context),
                ).result(timeout=60)
        except RuntimeError:
            return asyncio.run(
                llm_service._call_llm(rendered, context=context)
            )

    # ── Pass-through convenience ──────────────────────────────────────────────

    def to_pipeline_json(self) -> Dict[str, Any]:
        """Return the pipeline-optimised JSON view (in-memory dict)."""
        return self._result.to_pipeline_json()

    def to_branch_json(self) -> Dict[str, Any]:
        """Return the branch/mind-map JSON view (in-memory dict)."""
        return self._result.to_branch_json()

    def to_neo4j(self) -> Dict[str, Any]:
        """Return a Neo4j-compatible export payload (in-memory dict)."""
        return self._result.to_neo4j()

    def as_dict(self) -> Dict[str, Any]:
        """Return the full TraceResult as an in-memory dict without writing to disk.

        Use ``to_json()`` when you want a file written to disk.
        """
        payload = self._result.to_json()
        payload["key"] = self._key
        return payload

    @property
    def result(self) -> TraceResult:
        return self._result


# ─────────────────────────────────────────────────────────────────────────────
# Trace  –  holds one completed field trace, returned by Project.scan()
# ─────────────────────────────────────────────────────────────────────────────

class Trace:
    """Result of a single field scan."""

    def __init__(self, result: TraceResult, key: Optional[str] = None):
        self._result = result
        self._key = key  # propagated from Project.scan(key=...)

    def to_graph(self) -> Graph:
        """Return a Graph wrapper exposing to_html() / to_md() / to_json() / extend()."""
        return Graph(self._result, key=self._key)

    @property
    def result(self) -> TraceResult:
        return self._result

    @property
    def key(self) -> str:
        """Primary output key (uppercased field name or explicit key override)."""
        return (self._key or self._result.field_name).upper()

    def __repr__(self) -> str:
        r = self._result
        return (
            f"Trace(key={self.key!r}, field={r.field_name!r}, "
            f"origin={r.summary.origin.value}, "
            f"nodes={len(r.nodes)}, branches={len(r.branches)})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Project  –  returned by Scanner.load_project()
# ─────────────────────────────────────────────────────────────────────────────

class Project:
    """
    An indexed view of one or more repositories.

    Holds the pre-built index (java classes + xslt templates).
    Call .scan(field=...) to trace a single output field.
    """

    def __init__(
        self,
        index: Index,
        lib_repos: List[str],
        project_repos: List[str],
        default_trace_config: Optional[Dict[str, Any]] = None,
    ):
        self._index = index
        self._lib_repos = lib_repos
        self._project_repos = project_repos
        self._trace_config = default_trace_config or _default_trace_config()
        self._graph_builder = NxGraphBuilder()
        self._branch_engine = BranchTraceEngine()
        self._summarizer    = TraceSummarizer()

    # ── public API ────────────────────────────────────────────────────────────

    def scan(
        self,
        field: Optional[str] = None,
        *,
        key: Optional[str] = None,
        # allow the original typo as well (fiels=)
        fiels: Optional[str] = None,
        deep_scan_packages: Optional[List[str]] = None,
        extraction: Optional[List[str]] = None,
        transformation: Optional[List[str]] = None,
        load: Optional[List[str]] = None,
        downstream_packages: Optional[List[str]] = None,
        max_depth: int = 20,
        enable_condition_tracing: bool = True,
        enable_xslt_imports: bool = True,
    ) -> Trace:
        """
        Trace a single output field through extraction (XSLT) → transformation (Java).

        Parameters
        ----------
        field / fiels       : output field name, e.g. "N_CLEARED"
        key                 : primary output key — used as the filename stem for
                              all exports (html / md / json) and as the root node
                              label when graphs are composed via ``Graph.extend()``.
                              Defaults to ``field`` when omitted.
        deep_scan_packages  : packages to follow deeply, e.g. ["com.abc.*"]
        extraction          : file extensions for extraction phase  (default [".xslt", ".xsl"])
        transformation      : file extensions for transformation phase (default [".java"])
        load                : additional file extensions to load into the index
        downstream_packages : packages that consume this field (used by to_downstream())
        max_depth           : maximum call-chain depth to follow (default 20)
        enable_condition_tracing : extract conditional branch logic (default True)
        enable_xslt_imports     : follow xsl:import / xsl:include chains (default True)
        """
        field_name = field or fiels
        if not field_name:
            raise ValueError("scan() requires a field name via field= (or fiels=)")

        # key defaults to the field name; used for all output filenames
        output_key = key or field_name

        deep_scan_packages = deep_scan_packages or []
        extraction         = extraction or [".xslt", ".xsl"]
        transformation     = transformation or [".java"]

        # Merge deep_scan_packages into trace config so PackageFilter picks them up
        cfg = _merge_packages(self._trace_config, deep_scan_packages)

        trace_id = str(uuid.uuid4())
        _logger.info(
            f"Scanning field '{field_name}' | key='{output_key}' "
            f"| packages={deep_scan_packages}"
        )

        ctx = TraceContext(
            trace_id=trace_id,
            field_name=field_name,
            config=cfg,
            max_depth=max_depth,
            enable_condition_tracing=enable_condition_tracing,
            enable_xslt_imports=enable_xslt_imports,
        )

        engine = FieldTraceEngine(self._index, cfg)
        nodes, edges, origin = engine.trace(field_name, ctx)
        branches = self._branch_engine.build_branches(nodes, edges, ctx)
        graph    = self._graph_builder.build(nodes, edges)
        summary  = self._summarizer.summarize(field_name, origin, nodes, edges, branches)

        result = TraceResult(
            field_name=field_name,
            trace_id=trace_id,
            summary=summary,
            graph=graph,
            nodes=nodes,
            edges=edges,
            branches=branches,
            metadata={
                "key": output_key,
                "origin": origin.value,
                "lib_repos": self._lib_repos,
                "project_repos": self._project_repos,
                "deep_scan_packages": deep_scan_packages,
                "downstream_packages": downstream_packages or [],
                "merged_fields": [],
            },
            evidence_list=[n.evidence for n in nodes],
        )
        return Trace(result, key=output_key)

    def __repr__(self) -> str:
        return (
            f"Project(java_classes={len(self._index.java_classes)}, "
            f"xslt_templates={len(self._index.xslt_templates)}, "
            f"project_repos={self._project_repos})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Scanner  –  module-level singleton, mirrors the original `scanner` usage
# ─────────────────────────────────────────────────────────────────────────────

class Scanner:
    """
    Loads and indexes repositories, returns a Project.

    Usage
    -----
        project = scanner.load_project(lib_repos=[...], project_repos=[...])
    """

    def __init__(self):
        self._indexer = RepoIndexer()

    def load_project(
        self,
        lib_repos: Optional[List[str]] = None,
        project_repos: Optional[List[str]] = None,
        deep_scan_packages: Optional[List[str]] = None,
    ) -> Project:
        """
        Scan and index all repositories.

        lib_repos      – shared library / utility repos (indexed, not entry points)
        project_repos  – main project repos where traces begin
        """
        lib_repos     = lib_repos or []
        project_repos = project_repos or []

        all_repos = lib_repos + project_repos
        if not all_repos:
            raise ValueError("load_project() requires at least one repo path")

        _logger.info(
            f"Loading project: {len(lib_repos)} lib repos, "
            f"{len(project_repos)} project repos"
        )

        index = self._indexer.index(all_repos)

        cfg = _default_trace_config()
        if deep_scan_packages:
            cfg = _merge_packages(cfg, deep_scan_packages)

        return Project(
            index=index,
            lib_repos=lib_repos,
            project_repos=project_repos,
            default_trace_config=cfg,
        )


# Module-level singleton  ─  mirrors the original `scanner.load_project(...)` usage
scanner = Scanner()


# ─────────────────────────────────────────────────────────────────────────────
# Markdown exporter  (internal)
# ─────────────────────────────────────────────────────────────────────────────

class _MdExporter:
    """Renders a TraceResult as GitHub-flavoured Markdown."""

    def export(self, result: TraceResult) -> str:
        s = result.summary
        lines: List[str] = []

        # ── header ────────────────────────────────────────────────────────────
        lines += [
            f"# Field Lineage: `{result.field_name}`",
            "",
            f"| Property | Value |",
            f"|----------|-------|",
            f"| Trace ID | `{result.trace_id}` |",
            f"| Origin   | `{s.origin.value}` |",
            f"| Nodes    | {s.total_nodes} |",
            f"| Branches | {s.branch_count} |",
            f"| Has XSLT | {'Yes' if s.has_xslt else 'No'} |",
            f"| Has Java | {'Yes' if s.has_java else 'No'} |",
            "",
        ]

        # ── business explanation ──────────────────────────────────────────────
        lines += [
            "## Business Explanation",
            "",
            s.business_explanation or "_No explanation available._",
            "",
        ]

        # ── technical explanation ─────────────────────────────────────────────
        lines += [
            "## Technical Explanation",
            "",
            "```",
            s.technical_explanation or "_No explanation available._",
            "```",
            "",
        ]

        # ── pipeline steps ────────────────────────────────────────────────────
        lines += [
            "## Pipeline Steps",
            "",
            "| # | Step | Type | Class / Template | Method | File | Line |",
            "|---|------|------|-----------------|--------|------|------|",
        ]
        for i, node in enumerate(result.nodes, 1):
            t    = node.transformation_type.value if node.transformation_type else "—"
            ev   = node.evidence
            cls  = ev.class_or_template or "—"
            mth  = ev.method_or_template_name or "—"
            fp   = os.path.basename(ev.file_path) if ev.file_path else "—"
            ln   = str(ev.line_number) if ev.line_number else "—"
            lbl  = node.label.replace("|", "\\|")
            lines.append(f"| {i} | {lbl} | `{t}` | {cls} | {mth} | {fp} | {ln} |")
        lines.append("")

        # ── branches ─────────────────────────────────────────────────────────
        if result.branches:
            lines += [
                "## Branch Conditions",
                "",
                "| Branch | Condition | Outcome |",
                "|--------|-----------|---------|",
            ]
            for b in result.branches:
                cond    = b.condition.replace("|", "\\|")
                outcome = (b.outcome or "—").replace("|", "\\|")
                lines.append(f"| `{b.branch_id}` | {cond} | {outcome} |")
            lines.append("")

        # ── pipeline steps (plain text) ───────────────────────────────────────
        if s.pipeline_steps:
            lines += ["## Ordered Pipeline", ""]
            for i, step in enumerate(s.pipeline_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _default_trace_config() -> Dict[str, Any]:
    return {
        "trace": {
            "includePackages": ["*xxx*", "com.xxx.*"],
            "excludePackages": ["java.*", "javax.*", "org.springframework.*", "org.apache.*"],
            "stopPackages": [],
            "maxDepth": 20,
            "followInternalCallsOnly": True,
            "enableConditionTracing": True,
            "enableXsltImports": True,
        }
    }


def _merge_packages(config: Dict[str, Any], extra_packages: List[str]) -> Dict[str, Any]:
    """Return a copy of config with extra_packages added to includePackages."""
    import copy
    cfg = copy.deepcopy(config)
    existing = cfg.setdefault("trace", {}).setdefault("includePackages", [])
    for pkg in extra_packages:
        if pkg not in existing:
            existing.append(pkg)
    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# Quick smoke-test when run directly
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile, shutil, textwrap

    # ── Multi-module Maven project source files ───────────────────────────────
    #
    # Layout created below mirrors a real multi-module Maven project:
    #
    #   trade-service/          ← project_repos entry (root directory)
    #   ├── pom.xml             ← parent POM listing all sub-modules
    #   ├── xslt-module/        ← XSLT extraction layer
    #   │   ├── pom.xml
    #   │   └── src/main/resources/xslt/clearing.xsl
    #   ├── service-module/     ← Java transformation/enrichment layer
    #   │   ├── pom.xml
    #   │   └── src/main/java/com/xxx/clearing/ClearingService.java
    #   └── model-module/       ← shared domain model
    #       ├── pom.xml
    #       └── src/main/java/com/xxx/model/ClearingReport.java

    PARENT_POM = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project>
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.xxx</groupId>
          <artifactId>trade-service</artifactId>
          <version>1.0.0</version>
          <packaging>pom</packaging>
          <modules>
            <module>xslt-module</module>
            <module>service-module</module>
            <module>model-module</module>
          </modules>
        </project>
    """)

    XSLT_MODULE_POM = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project>
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.xxx</groupId>
          <artifactId>xslt-module</artifactId>
          <version>1.0.0</version>
        </project>
    """)

    SERVICE_MODULE_POM = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project>
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.xxx</groupId>
          <artifactId>service-module</artifactId>
          <version>1.0.0</version>
          <dependencies>
            <dependency>
              <groupId>com.xxx</groupId>
              <artifactId>model-module</artifactId>
              <version>1.0.0</version>
            </dependency>
          </dependencies>
        </project>
    """)

    MODEL_MODULE_POM = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project>
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.xxx</groupId>
          <artifactId>model-module</artifactId>
          <version>1.0.0</version>
        </project>
    """)

    XSLT = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
          <xsl:template name="buildClearingReport">
            <xsl:variable name="clearFlag" select="//trade/cleared"/>
            <xsl:call-template name="setClearedField">
              <xsl:with-param name="flag" select="$clearFlag"/>
            </xsl:call-template>
          </xsl:template>
          <xsl:template name="setClearedField">
            <xsl:param name="flag"/>
            <xsl:choose>
              <xsl:when test="$flag = 'true'"><N_CLEARED>Y</N_CLEARED></xsl:when>
              <xsl:otherwise><N_CLEARED>UNKNOWN</N_CLEARED></xsl:otherwise>
            </xsl:choose>
          </xsl:template>
        </xsl:stylesheet>
    """)

    JAVA_SVC = textwrap.dedent("""\
        package com.xxx.clearing;
        import com.xxx.model.Trade;
        import com.xxx.model.ClearingReport;
        public class ClearingService {
            public ClearingReport process(Trade trade) {
                ClearingReport report = new ClearingReport();
                report.setNCleared(trade.isCleared() ? "Y" : "N");
                report.setNSettlementDate(trade.getSettlementDate());
                return report;
            }
        }
    """)

    JAVA_REPORT = textwrap.dedent("""\
        package com.xxx.model;
        public class ClearingReport {
            private String nCleared;
            private String nSettlementDate;
            public void setNCleared(String v) { this.nCleared = v; }
            public void setNSettlementDate(String v) { this.nSettlementDate = v; }
        }
    """)

    tmpdir = tempfile.mkdtemp(prefix="dl_test_")
    try:
        # ── Build the multi-module Maven directory structure ───────────────────
        xslt_dir = os.path.join(tmpdir, "xslt-module",    "src", "main", "resources", "xslt")
        svc_dir  = os.path.join(tmpdir, "service-module", "src", "main", "java", "com", "xxx", "clearing")
        mdl_dir  = os.path.join(tmpdir, "model-module",   "src", "main", "java", "com", "xxx", "model")
        for d in (xslt_dir, svc_dir, mdl_dir):
            os.makedirs(d, exist_ok=True)

        # pom.xml files
        with open(os.path.join(tmpdir, "pom.xml"), "w") as f:                                   f.write(PARENT_POM)
        with open(os.path.join(tmpdir, "xslt-module",    "pom.xml"), "w") as f:                 f.write(XSLT_MODULE_POM)
        with open(os.path.join(tmpdir, "service-module", "pom.xml"), "w") as f:                 f.write(SERVICE_MODULE_POM)
        with open(os.path.join(tmpdir, "model-module",   "pom.xml"), "w") as f:                 f.write(MODEL_MODULE_POM)

        # Source files
        with open(os.path.join(xslt_dir, "clearing.xsl"), "w") as f:         f.write(XSLT)
        with open(os.path.join(svc_dir,  "ClearingService.java"), "w") as f: f.write(JAVA_SVC)
        with open(os.path.join(mdl_dir,  "ClearingReport.java"),  "w") as f: f.write(JAVA_REPORT)

        # ── Usage: pass the project root directory (not individual modules) ───
        #
        #   lib_repos     = root directories of shared library Maven projects
        #   project_repos = root directories of main application Maven projects
        #
        # The scanner recursively discovers all .java and .xsl/.xslt files
        # within the provided roots, honoring the multi-module Maven layout.
        lib_repos          = []            # no shared library projects in this demo
        project_repos      = [tmpdir]      # root of the multi-module Maven project
        deep_scan_packages = ["com.xxx.*"]
        extraction         = [".xslt", ".xsl"]
        transformation     = [".java"]
        load               = [".java"]
        downstream_packages= ["com.xxx.*"]
        fields             = ["N_CLEARED", "N_SETTLEMENT_DATE"]

        project = scanner.load_project(
            lib_repos=lib_repos,
            project_repos=project_repos,
            deep_scan_packages=deep_scan_packages,
        )
        print(project)

        graphs: List[Graph] = []

        for field in fields:
            print(f"\n── Tracing: {field} ──")

            # key= sets the primary output name for all exports (html / md / json).
            # All output files will be named after the key, not the raw field name.
            trace = project.scan(
                key=field,                             # primary output key
                field=field,
                deep_scan_packages=deep_scan_packages,
                extraction=extraction,
                transformation=transformation,
                load=load,
                downstream_packages=downstream_packages,
            )
            print(trace)

            graph = trace.to_graph()
            graphs.append(graph)

        # ── Compose graphs: merge all traces into the first one ───────────────
        # graph.extend() merges nodes, edges, branches and the NX graph in-place.
        # The primary key (and output filename) stays that of the first graph.
        if len(graphs) > 1:
            base_graph = graphs[0]
            for other in graphs[1:]:
                base_graph.extend(graph=other)
            combined = base_graph
        else:
            combined = graphs[0]

        # ── Export the combined / individual graph ────────────────────────────
        html_path = combined.to_html()
        md_path   = combined.to_md()
        json_path = combined.to_json()   # NEW — saves <KEY>.json to disk

        # ── LLM-powered analysis (stub — wire llm_service._call_llm to a real LLM) ──
        # Business derivation: plain-English explanation of how the field is populated
        bussiness_derivation = combined.to_buissness_derivation("business_derivation")

        # Reporting logic: how this field drives report inclusion / category selection
        reporting_logic = combined.to_reporting_logic()

        # Enrichment logic: extraction → enrichment → override chain
        enrichment_logic = combined.to_enrichment_logic()

        # Downstream impact: which fields, reports and dashboards depend on this field
        downstream = combined.to_downstream(
            downstream_name="downstream_system",
            downstream_packages=downstream_packages,
        )

        # Concrete worked examples for each conditional branch
        examples = combined.to_example()

        # Operational runbook: happy path, fallbacks, overrides, monitoring
        operations = combined.to_operation()

        print(f"  HTML → {html_path}")
        print(f"  MD   → {md_path}")
        print(f"  JSON → {json_path}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\nDone.")
