"""Quick trace — simple functional API for validating lineage.

Core function: trace_project() — scans a main project, identifies unresolved
references to library classes/constants, then searches library projects for
those references. The graph starts from the main project and drills down
into every library.

Use `targets` to trace only specific fields, methods, or variables:

    result = trace_project(
        main="/code/my-app",
        libs=["/code/lib-fields"],
        targets=["N_EFFECTIVE_DATE"],       # only this field's lineage
    )

    # Or trace a method
    result = trace_project(main="/code/my-app", targets=["processIncoming"])

    # Or trace multiple things at once
    result = trace_project(
        main="/code/my-app",
        targets=["N_TRADE_ID", "N_EFFECTIVE_DATE", "processSettlement"],
    )

    # Or filter after the fact
    full = trace_project(main="/code/my-app", libs=[...])
    subset = full.filter("N_TRADE_ID")

Parsers are pluggable via a file-extension registry:

    from orchestrator.quick_trace import register_parser
    register_parser(".groovy", MyGroovyParser)
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Union

from orchestrator.models import (
    JavaFinding, LineageEdge, LineageNode, StitchedLineage, XsltFinding,
)
from orchestrator.parsers.java_parser import JavaParser
from orchestrator.parsers.xslt_parser import XsltParser
from orchestrator.scanner import ModuleScanner
from orchestrator.stitcher import Stitcher, _build_match_keys
from orchestrator.storage.local_graph_pyvis import PyVisGraphProvider


# ---------------------------------------------------------------------------
# Pluggable parser registry
# ---------------------------------------------------------------------------


class FileParser(Protocol):
    """Protocol for any file parser. Must accept repo_name and have parse_file."""

    def __init__(self, repo_name: str = "") -> None: ...
    def parse_file(self, file_path: Path) -> list: ...


# Extension -> parser class mapping.  .java and .xsl/.xslt are built-in.
# Users can add more via register_parser().
_PARSER_REGISTRY: dict[str, type] = {
    ".java": JavaParser,
    ".xsl": XsltParser,
    ".xslt": XsltParser,
}


def register_parser(extension: str, parser_class: type) -> None:
    """Register a parser class for a file extension.

    Args:
        extension: File extension including the dot, e.g. ".groovy"
        parser_class: Must have __init__(repo_name: str) and parse_file(Path) -> list
    """
    _PARSER_REGISTRY[extension.lower()] = parser_class


def get_parser_for_file(file_path: Path, repo_name: str = "") -> object | None:
    """Get the right parser instance for a file based on its extension."""
    ext = file_path.suffix.lower()
    cls = _PARSER_REGISTRY.get(ext)
    if cls is None:
        return None
    return cls(repo_name=repo_name)


def supported_extensions() -> list[str]:
    """Return list of currently registered file extensions."""
    return sorted(_PARSER_REGISTRY.keys())


# ---------------------------------------------------------------------------
# TraceResult
# ---------------------------------------------------------------------------


@dataclass
class TraceResult:
    """Result of a trace — wraps StitchedLineage with convenience methods."""

    lineage: StitchedLineage
    java_findings: list[JavaFinding] = field(default_factory=list)
    xslt_findings: list[XsltFinding] = field(default_factory=list)
    unresolved_classes: set[str] = field(default_factory=set)
    resolved_from_libs: dict[str, str] = field(default_factory=dict)  # class -> lib_name

    @property
    def nodes(self):
        return self.lineage.nodes

    @property
    def edges(self):
        return self.lineage.edges

    @property
    def node_count(self) -> int:
        return len(self.lineage.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.lineage.edges)

    def edges_by_type(self, edge_type: str) -> list:
        return [e for e in self.lineage.edges if e.edge_type.value == edge_type]

    def nodes_by_type(self, node_type: str) -> list:
        return [n for n in self.lineage.nodes if n.node_type.value == node_type]

    def print_summary(self) -> None:
        print(f"Nodes: {self.node_count}, Edges: {self.edge_count}")
        print(f"Java findings: {len(self.java_findings)}")
        print(f"XSLT findings: {len(self.xslt_findings)}")

        if self.resolved_from_libs:
            print(f"Resolved from libraries:")
            for cls, lib in sorted(self.resolved_from_libs.items()):
                print(f"  {cls} <- {lib}")
        if self.unresolved_classes:
            print(f"Still unresolved: {', '.join(sorted(self.unresolved_classes))}")

        edge_types: dict[str, int] = {}
        for e in self.lineage.edges:
            edge_types[e.edge_type.value] = edge_types.get(e.edge_type.value, 0) + 1
        if edge_types:
            print("Edges by type:")
            for t, c in sorted(edge_types.items()):
                print(f"  {t}: {c}")

        node_types: dict[str, int] = {}
        for n in self.lineage.nodes:
            node_types[n.node_type.value] = node_types.get(n.node_type.value, 0) + 1
        if node_types:
            print("Nodes by type:")
            for t, c in sorted(node_types.items()):
                print(f"  {t}: {c}")

    def print_nodes(self) -> None:
        for n in self.lineage.nodes:
            print(f"  [{n.node_type.value}] {n.id}  label={n.label}")

    def print_edges(self) -> None:
        for e in self.lineage.edges:
            print(f"  {e.source_id}  --[{e.edge_type.value}]-->  {e.target_id}")

    def to_json(self, path: Union[str, Path]) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        provider = PyVisGraphProvider(output_dir=path.parent)
        provider.ingest_lineage(self.lineage)
        data = provider.export_node_link_json()
        path.write_text(json.dumps(data, indent=2))
        print(f"JSON written to {path}")
        return path

    def to_html(self, path: Union[str, Path]) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        provider = PyVisGraphProvider(output_dir=path.parent)
        provider.ingest_lineage(self.lineage)
        provider.persist()
        print(f"HTML written to {path.parent}")
        return path

    def filter(self, *targets: str, max_depth: int = 15) -> "TraceResult":
        """Return a new TraceResult containing only the subgraph for the given targets.

        Targets can be field names, method names, class names, or variable names.
        Matches against node IDs, labels, and properties using fuzzy matching.

        Args:
            targets:   One or more names to trace, e.g. "N_EFFECTIVE_DATE", "processIncoming"
            max_depth: Max BFS hops from seed nodes (default 15)

        Returns:
            New TraceResult with filtered lineage.
        """
        filtered = _filter_lineage(self.lineage, list(targets), max_depth=max_depth)
        return TraceResult(
            lineage=filtered,
            java_findings=self.java_findings,
            xslt_findings=self.xslt_findings,
            unresolved_classes=self.unresolved_classes,
            resolved_from_libs=self.resolved_from_libs,
        )


# ---------------------------------------------------------------------------
# Subgraph filtering
# ---------------------------------------------------------------------------


def _match_node(node: LineageNode, targets: list[str], target_keys: set[str]) -> bool:
    """Check if a node matches any of the target names.

    Matches against:
      - Node label (exact or contains)
      - Node ID segments
      - Properties: bare_name, output_element, xpath, qualifier
      - Canonical match keys (same fuzzy matching used by the stitcher)
    """
    # Collect all searchable text from this node
    searchable: set[str] = set()
    searchable.add(node.label.lower().strip('"'))
    searchable.add(node.id.lower())

    # ID segments: "java::method::com.acme.TradeService::processIncoming" -> each part
    for seg in node.id.split("::"):
        searchable.add(seg.lower())
        # Also the simple class name: com.acme.TradeService -> TradeService
        if "." in seg:
            searchable.add(seg.rsplit(".", 1)[-1].lower())

    # Properties
    for prop_key in ("bare_name", "output_element", "xpath", "qualifier", "owner"):
        val = node.properties.get(prop_key, "")
        if val:
            searchable.add(str(val).lower().strip('"'))

    # Check: does any target appear in the node's searchable text?
    for t in targets:
        t_lower = t.lower()
        # Exact match on any searchable value
        if t_lower in searchable:
            return True
        # Substring match on label or ID
        if t_lower in node.label.lower() or t_lower in node.id.lower():
            return True

    # Check canonical match keys overlap
    node_keys: set[str] = set()
    for s in searchable:
        node_keys |= _build_match_keys(s)

    return bool(node_keys & target_keys)


def _filter_lineage(
    lineage: StitchedLineage,
    targets: list[str],
    max_depth: int = 15,
    type_filter: set[str] | None = None,
) -> StitchedLineage:
    """Extract the subgraph connected to the target names.

    1. Find all seed nodes that match any target
    2. BFS walk from seeds to collect connected nodes
    3. Return a new StitchedLineage with only those nodes/edges
    """
    if not targets:
        return lineage

    # Build canonical keys for all targets for fuzzy matching
    target_keys: set[str] = set()
    for t in targets:
        target_keys |= _build_match_keys(t)

    # Step 1: Find seed nodes
    node_by_id: dict[str, LineageNode] = {n.id: n for n in lineage.nodes}
    seed_ids: set[str] = set()

    for node in lineage.nodes:
        # Apply type filter if specified
        if type_filter and node.node_type.value not in type_filter:
            continue
        if _match_node(node, targets, target_keys):
            seed_ids.add(node.id)

    if not seed_ids:
        print(f"  Warning: no nodes matched targets {targets}")
        return StitchedLineage(nodes=[], edges=[])

    # Step 2: Build adjacency (undirected) and BFS from seeds
    adj: dict[str, set[str]] = defaultdict(set)
    for edge in lineage.edges:
        adj[edge.source_id].add(edge.target_id)
        adj[edge.target_id].add(edge.source_id)

    reachable: set[str] = set()
    queue: list[tuple[str, int]] = [(sid, 0) for sid in seed_ids]

    while queue:
        nid, depth = queue.pop(0)
        if nid in reachable or depth > max_depth:
            continue
        reachable.add(nid)
        for neighbor in adj.get(nid, []):
            if neighbor not in reachable:
                queue.append((neighbor, depth + 1))

    # Step 3: Build filtered lineage
    filtered_nodes = [n for n in lineage.nodes if n.id in reachable]
    filtered_edges = [
        e for e in lineage.edges
        if e.source_id in reachable and e.target_id in reachable
    ]

    return StitchedLineage(nodes=filtered_nodes, edges=filtered_edges)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_file_auto(
    file_path: Path, repo_name: str,
    java_findings: list, xslt_findings: list,
) -> None:
    """Parse a single file using the right parser based on file extension."""
    parser = get_parser_for_file(file_path, repo_name=repo_name)
    if parser is None:
        return  # unsupported extension, skip

    findings = parser.parse_file(file_path)
    if isinstance(parser, XsltParser):
        xslt_findings.extend(findings)
    else:
        java_findings.extend(findings)


def _find_classes_defined(findings: list[JavaFinding]) -> set[str]:
    """Extract all class names defined in the codebase from findings."""
    classes: set[str] = set()
    for f in findings:
        if f.class_name:
            # Full qualified: com.acme.app.TradeService -> TradeService
            classes.add(f.class_name)
            simple = f.class_name.rsplit(".", 1)[-1]
            classes.add(simple)
    return classes


def _find_unresolved_refs(
    findings: list[JavaFinding], defined_classes: set[str]
) -> set[str]:
    """Find constant qualifiers and method call targets not defined in the main project.

    E.g. if code uses MessageKey.N_TRADE_ID but MessageKey is not defined
    in the main project, "MessageKey" is unresolved.
    """
    unresolved: set[str] = set()
    # Standard library / framework classes to ignore
    ignore = {
        "System", "Math", "Integer", "Long", "Double", "String", "Float",
        "Boolean", "Object", "Class", "Thread", "Runtime", "Byte", "Short",
        "Character", "Void", "Number",
        "Collections", "Arrays", "Optional", "List", "Map", "Set",
        "HashMap", "ArrayList", "LinkedList", "HashSet", "TreeMap",
        "Logger", "LoggerFactory", "LOG", "LOGGER", "log", "logger",
        "Transformer", "TransformerFactory", "StreamSource",
        "mapper", "factory", "transformer", "builder",
    }

    for f in findings:
        if f.finding_type == "constant_ref" and f.target_class:
            if f.target_class not in defined_classes and f.target_class not in ignore:
                unresolved.add(f.target_class)

        if f.finding_type == "method_call" and f.target_class:
            if f.target_class not in defined_classes and f.target_class not in ignore:
                # Only if it looks like a class name (starts with uppercase)
                if f.target_class[0].isupper():
                    unresolved.add(f.target_class)

    return unresolved


def _search_lib_for_classes(
    lib_path: Path, lib_name: str, target_classes: set[str],
) -> tuple[list[Path], set[str]]:
    """Search a library project for files that define any of the target classes.

    Returns (matching_files, found_classes).
    """
    matching: list[Path] = []
    found: set[str] = set()

    if not lib_path.exists():
        return matching, found

    import re
    re_class = re.compile(
        r"(?:public|private|protected)?\s*(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)"
    )

    for java_file in lib_path.rglob("*.java"):
        text = java_file.read_text(errors="replace")
        for m in re_class.finditer(text):
            class_name = m.group(1)
            if class_name in target_classes:
                matching.append(java_file)
                found.add(class_name)
                break  # one match per file is enough

    return matching, found


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def trace_project(
    main: Union[str, Path],
    libs: list[Union[str, Path]] = None,
    main_name: str = "",
    lib_names: list[str] = None,
    targets: list[str] = None,
) -> TraceResult:
    """Trace lineage starting from a main project, drilling into library projects.

    Flow:
      1. Scan the main project (auto-discovers modules, Java + XSLT files)
      2. Parse all discovered files using extension-based parser dispatch
      3. Identify unresolved references (classes not defined in main)
      4. Search each library project for those classes
      5. Parse only the matching library files
      6. Stitch everything into one graph
      7. If targets given, filter to only the subgraph for those targets

    Args:
        main:       Path to the main multi-module project root
        libs:       List of paths to library project roots
        main_name:  Name for the main project (default: directory name)
        lib_names:  Names for each library (default: directory names)
        targets:    Field/method/class names to trace (None = trace everything)

    Returns:
        TraceResult with full lineage and resolution metadata.
    """
    main_path = Path(main)
    libs = [Path(p) for p in (libs or [])]
    if not main_name:
        main_name = main_path.name
    if lib_names is None:
        lib_names = [p.name for p in libs]

    scanner = ModuleScanner()
    all_java: list[JavaFinding] = []
    all_xslt: list[XsltFinding] = []

    # ── Step 1: Scan main project ────────────────────────────────────────
    project = scanner.scan_project(main_path, name=main_name)
    print(f"Main project: {project.summary()}")

    for mod in project.modules:
        print(f"  Module: {mod.name}")
        repo_tag = mod.name

        # Parse each file with the right parser based on extension
        for jf in mod.java_files:
            _parse_file_auto(jf, repo_tag, all_java, all_xslt)
        for xf in mod.xslt_files:
            _parse_file_auto(xf, repo_tag, all_java, all_xslt)

    print(f"  Parsed: {len(all_java)} java findings, {len(all_xslt)} xslt findings")

    # ── Step 2: Find unresolved references ───────────────────────────────
    defined_classes = _find_classes_defined(all_java)
    unresolved = _find_unresolved_refs(all_java, defined_classes)

    resolved_from_libs: dict[str, str] = {}
    still_unresolved = set(unresolved)

    if unresolved:
        print(f"  Unresolved references: {', '.join(sorted(unresolved))}")

    # ── Step 3: Search libraries for unresolved classes ──────────────────
    if unresolved and libs:
        for i, lib_path in enumerate(libs):
            lib_name = lib_names[i] if i < len(lib_names) else lib_path.name

            matching_files, found_classes = _search_lib_for_classes(
                lib_path, lib_name, still_unresolved
            )

            if found_classes:
                print(f"  Library [{lib_name}]: found {', '.join(sorted(found_classes))}")
                for cls in found_classes:
                    resolved_from_libs[cls] = lib_name
                still_unresolved -= found_classes

                # Parse those library files
                for lf in matching_files:
                    _parse_file_auto(lf, lib_name, all_java, all_xslt)

            if not still_unresolved:
                break  # all resolved

    if still_unresolved:
        print(f"  Still unresolved: {', '.join(sorted(still_unresolved))}")

    # ── Step 4: Stitch ───────────────────────────────────────────────────
    lineage = Stitcher().stitch(all_java, all_xslt)

    # ── Step 5: Filter to targets (if specified) ─────────────────────────
    if targets:
        print(f"  Filtering to targets: {', '.join(targets)}")
        lineage = _filter_lineage(lineage, targets)
        print(f"  Filtered: {len(lineage.nodes)} nodes, {len(lineage.edges)} edges")

    return TraceResult(
        lineage=lineage,
        java_findings=all_java,
        xslt_findings=all_xslt,
        unresolved_classes=still_unresolved,
        resolved_from_libs=resolved_from_libs,
    )


def trace(
    name: str,
    type: str = "any",
    search_type: str = "like",
    project: Union[str, Path, list] = None,
    libs: list[Union[str, Path]] = None,
) -> TraceResult:
    """Single entry point — trace a specific field, method, or class by name.

    Args:
        name:        What to search for, e.g. "N_EFFECTIVE_DATE", "processIncoming", "TradeService"
        type:        Filter by kind: "variable", "method", "class", "field", or "any" (default)
        search_type: "like" (fuzzy/substring, default) or "exact" (strict match)
        project:     Main project path(s). Can be a single path or list of paths.
        libs:        Library project paths for dependency resolution.

    Returns:
        TraceResult with only the lineage for the matched target.

    Examples:
        # Trace a field across main project + libraries
        trace("N_EFFECTIVE_DATE", type="variable", project="/code/my-app", libs=["/code/lib-fields"])

        # Trace a method
        trace("processIncoming", type="method", project="/code/my-app")

        # Trace a class
        trace("TradeService", type="class", project="/code/my-app")

        # Fuzzy match (default) — finds N_EFFECTIVE_DATE, effectiveDate, etc.
        trace("effective_date", search_type="like", project="/code/my-app")

        # Exact match — only N_EFFECTIVE_DATE
        trace("N_EFFECTIVE_DATE", search_type="exact", project="/code/my-app")

        # Multiple projects as main
        trace("N_TRADE_ID", project=["/code/app-a", "/code/app-b"], libs=["/code/lib"])
    """
    # Normalize project to list
    if project is None:
        project = ["."]
    elif isinstance(project, (str, Path)):
        project = [project]
    project_paths = [Path(p) for p in project]
    libs = [Path(p) for p in (libs or [])]

    # Step 1: Scan and parse all projects + libs (full graph first)
    scanner = ModuleScanner()
    all_java: list[JavaFinding] = []
    all_xslt: list[XsltFinding] = []
    resolved_from_libs: dict[str, str] = {}
    still_unresolved: set[str] = set()

    for proj_path in project_paths:
        proj_name = proj_path.name
        proj = scanner.scan_project(proj_path, name=proj_name)
        print(f"Project: {proj.summary()}")

        for mod in proj.modules:
            for jf in mod.java_files:
                _parse_file_auto(jf, mod.name, all_java, all_xslt)
            for xf in mod.xslt_files:
                _parse_file_auto(xf, mod.name, all_java, all_xslt)

    # Resolve library dependencies
    if libs:
        defined_classes = _find_classes_defined(all_java)
        unresolved = _find_unresolved_refs(all_java, defined_classes)
        still_unresolved = set(unresolved)

        for lib_path in libs:
            lib_name = lib_path.name
            matching_files, found_classes = _search_lib_for_classes(
                lib_path, lib_name, still_unresolved
            )
            if found_classes:
                for cls in found_classes:
                    resolved_from_libs[cls] = lib_name
                still_unresolved -= found_classes
                for lf in matching_files:
                    _parse_file_auto(lf, lib_name, all_java, all_xslt)

    # Step 2: Stitch full graph
    lineage = Stitcher().stitch(all_java, all_xslt)

    # Step 3: Filter by type and search_type
    targets = [name]

    # Type-based pre-filter: narrow seed nodes by node type
    type_filter = _TYPE_MAP.get(type.lower(), None)

    if search_type.lower() == "exact":
        filtered = _filter_lineage_exact(lineage, name, type_filter=type_filter)
    else:
        filtered = _filter_lineage(lineage, targets, type_filter=type_filter)

    print(f"  trace(\"{name}\", type=\"{type}\", search_type=\"{search_type}\")")
    print(f"  Result: {len(filtered.nodes)} nodes, {len(filtered.edges)} edges")

    return TraceResult(
        lineage=filtered,
        java_findings=all_java,
        xslt_findings=all_xslt,
        unresolved_classes=still_unresolved,
        resolved_from_libs=resolved_from_libs,
    )


# Type name -> set of NodeType values that match
_TYPE_MAP: dict[str, set[str]] = {
    "variable": {"JAVA_FIELD", "JAVA_CONSTANT", "XSLT_FIELD"},
    "field": {"JAVA_FIELD", "JAVA_CONSTANT", "XSLT_FIELD"},
    "method": {"JAVA_METHOD"},
    "class": {"JAVA_CLASS", "DTO"},
    "xslt": {"XSLT_FILE", "XSLT_TEMPLATE", "XSLT_FIELD"},
    "any": None,  # no filter
}


def _filter_lineage_exact(
    lineage: StitchedLineage,
    name: str,
    type_filter: set[str] | None = None,
    max_depth: int = 15,
) -> StitchedLineage:
    """Filter lineage with exact name matching (no fuzzy canonical forms)."""
    node_by_id: dict[str, LineageNode] = {n.id: n for n in lineage.nodes}
    seed_ids: set[str] = set()
    name_lower = name.lower()

    for node in lineage.nodes:
        # Type filter
        if type_filter and node.node_type.value not in type_filter:
            continue

        # Exact match on label, bare_name, or ID segment
        searchable = {
            node.label.lower().strip('"'),
            node.properties.get("bare_name", "").lower(),
            node.properties.get("output_element", "").lower(),
        }
        # Last segment of ID
        last_seg = node.id.rsplit("::", 1)[-1].lower()
        if "." in last_seg:
            searchable.add(last_seg.rsplit(".", 1)[-1])
        searchable.add(last_seg)

        if name_lower in searchable:
            seed_ids.add(node.id)

    if not seed_ids:
        print(f"  Warning: no exact match for \"{name}\"")
        return StitchedLineage(nodes=[], edges=[])

    # BFS from seeds
    adj: dict[str, set[str]] = defaultdict(set)
    for edge in lineage.edges:
        adj[edge.source_id].add(edge.target_id)
        adj[edge.target_id].add(edge.source_id)

    reachable: set[str] = set()
    queue = [(sid, 0) for sid in seed_ids]
    while queue:
        nid, depth = queue.pop(0)
        if nid in reachable or depth > max_depth:
            continue
        reachable.add(nid)
        for nb in adj.get(nid, []):
            if nb not in reachable:
                queue.append((nb, depth + 1))

    return StitchedLineage(
        nodes=[n for n in lineage.nodes if n.id in reachable],
        edges=[e for e in lineage.edges if e.source_id in reachable and e.target_id in reachable],
    )


def trace_files(
    java_files: list[Union[str, Path]] = None,
    xslt_files: list[Union[str, Path]] = None,
    repo_name: str = "default",
) -> TraceResult:
    """Trace lineage from explicit file lists (simple mode).

    Files are dispatched to the correct parser by extension.
    """
    all_files = []
    for f in (java_files or []):
        all_files.append(Path(f))
    for f in (xslt_files or []):
        all_files.append(Path(f))

    all_java: list[JavaFinding] = []
    all_xslt: list[XsltFinding] = []

    for fp in all_files:
        if not fp.exists():
            print(f"  Warning: file not found: {fp}")
            continue
        _parse_file_auto(fp, repo_name, all_java, all_xslt)

    lineage = Stitcher().stitch(all_java, all_xslt)
    return TraceResult(lineage=lineage, java_findings=all_java, xslt_findings=all_xslt)


def trace_repos(
    repos: list[dict],
) -> TraceResult:
    """Trace lineage across multiple repos/projects.

    Each repo dict supports:
        name:         Repo/project name (required)
        path:         Root directory (required)
        java_files:   Explicit list of .java files (optional)
        xslt_files:   Explicit list of .xsl/.xslt files (optional)
        java_dirs:    Directories to scan for .java files (optional)
        xslt_dirs:    Directories to scan for .xsl/.xslt files (optional)
        scan:         If True, auto-discover all files under path (optional)
        project_scan: If True, auto-discover modules under path (optional)
        libs:         List of library paths to resolve unresolved refs (optional)
    """
    scanner = ModuleScanner()
    all_java: list[JavaFinding] = []
    all_xslt: list[XsltFinding] = []

    for repo in repos:
        name = repo["name"]
        root = Path(repo["path"])

        # --- Project scan with library resolution ---
        if repo.get("project_scan"):
            libs = [Path(p) for p in repo.get("libs", [])]
            if libs:
                # Use trace_project for dependency-aware scanning
                result = trace_project(main=root, libs=libs, main_name=name)
                all_java.extend(result.java_findings)
                all_xslt.extend(result.xslt_findings)
            else:
                project = scanner.scan_project(root, name=name)
                print(f"  [{name}] {project.summary()}")
                for mod in project.modules:
                    for jf in mod.java_files:
                        _parse_file_auto(jf, mod.name, all_java, all_xslt)
                    for xf in mod.xslt_files:
                        _parse_file_auto(xf, mod.name, all_java, all_xslt)
            continue

        # --- Auto-scan ---
        if repo.get("scan"):
            module = scanner.scan(root, name=name)
            print(f"  [{name}] {module.summary()}")
            for jf in module.java_files:
                _parse_file_auto(jf, name, all_java, all_xslt)
            for xf in module.xslt_files:
                _parse_file_auto(xf, name, all_java, all_xslt)
            continue

        # --- Explicit files (dispatched by extension) ---
        for fp in repo.get("java_files", []) + repo.get("xslt_files", []):
            fp = Path(fp)
            if not fp.exists():
                print(f"  [{name}] Warning: {fp} not found")
                continue
            _parse_file_auto(fp, name, all_java, all_xslt)

        # --- Explicit directories ---
        java_parser = JavaParser(repo_name=name)
        xslt_parser = XsltParser(repo_name=name)
        for jd in repo.get("java_dirs", []):
            jd = Path(jd)
            if jd.exists():
                all_java.extend(java_parser.parse_directory(jd))
        for xd in repo.get("xslt_dirs", []):
            xd = Path(xd)
            if xd.exists():
                all_xslt.extend(xslt_parser.parse_directory(xd))

    lineage = Stitcher().stitch(all_java, all_xslt)
    return TraceResult(lineage=lineage, java_findings=all_java, xslt_findings=all_xslt)
