"""Quick trace — simple functional API for validating lineage.

Core function: trace_project() — scans a main project, identifies unresolved
references to library classes/constants, then searches library projects for
those references. The graph starts from the main project and drills down
into every library.

Parsers are pluggable via a file-extension registry. To add a new parser
(e.g. for .groovy files), register it before calling trace:

    from orchestrator.quick_trace import register_parser
    register_parser(".groovy", MyGroovyParser)

Usage:

    from orchestrator.quick_trace import trace_project

    result = trace_project(
        main="/code/my-app",                  # multi-module main project
        libs=["/code/lib-fields", "/code/lib-transform"],  # library jars/sources
    )

    result.print_summary()
    result.to_html("output/lineage.html")
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Union

from orchestrator.models import JavaFinding, StitchedLineage, XsltFinding
from orchestrator.parsers.java_parser import JavaParser
from orchestrator.parsers.xslt_parser import XsltParser
from orchestrator.scanner import ModuleScanner
from orchestrator.stitcher import Stitcher
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
) -> TraceResult:
    """Trace lineage starting from a main project, drilling into library projects.

    Flow:
      1. Scan the main project (auto-discovers modules, Java + XSLT files)
      2. Parse all discovered files using extension-based parser dispatch
      3. Identify unresolved references (classes not defined in main)
      4. Search each library project for those classes
      5. Parse only the matching library files
      6. Stitch everything into one graph

    Args:
        main:       Path to the main multi-module project root
        libs:       List of paths to library project roots
        main_name:  Name for the main project (default: directory name)
        lib_names:  Names for each library (default: directory names)

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

    return TraceResult(
        lineage=lineage,
        java_findings=all_java,
        xslt_findings=all_xslt,
        unresolved_classes=still_unresolved,
        resolved_from_libs=resolved_from_libs,
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
