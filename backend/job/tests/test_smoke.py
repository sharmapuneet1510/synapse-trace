"""Smoke tests: single-repo, multi-repo, auto-scan, and field variation matching."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestrator.models import RepoConfig
from orchestrator.parsers.java_parser import JavaParser
from orchestrator.parsers.xslt_parser import XsltParser
from orchestrator.quick_trace import trace, trace_project, trace_files, supported_extensions
from orchestrator.scanner import ModuleScanner
from orchestrator.stitcher import Stitcher, _build_match_keys
from orchestrator.storage.local_graph_pyvis import PyVisGraphProvider

FIXTURES = Path(__file__).parent / "fixtures" / "sample"
MULTI_REPO = Path(__file__).parent / "fixtures" / "multi-repo"
MIXED_MODULE = Path(__file__).parent / "fixtures" / "mixed-module"
MULTI_PROJECT = Path(__file__).parent / "fixtures" / "multi-project"
APP_WITH_LIBS = Path(__file__).parent / "fixtures" / "app-with-libs"


# ---- Field variation matching tests ----

def test_build_match_keys():
    """_build_match_keys should produce all canonical forms."""
    keys = _build_match_keys("MessageKey.N_EFFECTIVE_DATE")
    assert "n_effective_date" in keys
    assert "neffectivedate" in keys or "nEffectiveDate".lower() in keys
    # Should also strip the single-letter prefix
    assert "effective_date" in keys
    assert "effectivedate" in keys

    keys2 = _build_match_keys("effectiveDate")
    assert "effective_date" in keys2
    assert "effectivedate" in keys2

    keys3 = _build_match_keys("N_COUNTERPARTY_2")
    assert "n_counterparty_2" in keys3

    # They should overlap for matching
    overlap = keys & keys2
    assert len(overlap) > 0, f"Should have overlap: {keys} vs {keys2}"


def test_java_parser():
    parser = JavaParser(repo_name="test")
    findings = parser.parse_directory(FIXTURES / "java")
    assert len(findings) > 0

    unmarshals = [f for f in findings if f.finding_type == "unmarshal"]
    assert len(unmarshals) >= 2

    mappings = [f for f in findings if f.finding_type == "field_mapping"]
    assert len(mappings) >= 4

    for f in findings:
        assert f.repo_name == "test"
        assert f.meta.file_path
        assert f.meta.line_number > 0
        assert f.meta.md5_hash


def test_java_parser_constants():
    """Parser should detect constant references and string literals."""
    parser = JavaParser(repo_name="lib")
    findings = parser.parse_directory(MULTI_REPO / "lib-common" / "java")

    const_refs = [f for f in findings if f.finding_type == "constant_ref"]
    string_lits = [f for f in findings if f.finding_type == "string_literal"]

    # MessageKey.java and FieldNames.java don't use constants themselves,
    # but they define string literals like "N_EFFECTIVE_DATE"
    assert len(string_lits) > 0, f"Should find string literal field keys, got {len(string_lits)}"

    # Now check the app-trade which references MessageKey.N_EFFECTIVE_DATE
    app_parser = JavaParser(repo_name="app")
    app_findings = app_parser.parse_directory(MULTI_REPO / "app-trade" / "java")

    app_consts = [f for f in app_findings if f.finding_type == "constant_ref"]
    app_literals = [f for f in app_findings if f.finding_type == "string_literal"]

    assert len(app_consts) >= 4, (
        f"Should find MessageKey.N_EFFECTIVE_DATE etc, got {len(app_consts)}: "
        f"{[(c.target_class, c.field_name) for c in app_consts]}"
    )
    assert len(app_literals) >= 2, f"Should find string literal keys, got {len(app_literals)}"


def test_xslt_parser():
    parser = XsltParser(repo_name="test")
    findings = parser.parse_directory(FIXTURES / "xslt")
    assert len(findings) > 0

    value_ofs = [f for f in findings if f.finding_type == "value_of"]
    assert len(value_ofs) >= 4

    calls = [f for f in findings if f.finding_type == "template_call"]
    assert len(calls) >= 1

    for f in findings:
        assert f.repo_name == "test"


def test_stitcher_single_repo():
    java_parser = JavaParser()
    xslt_parser = XsltParser()
    stitcher = Stitcher()

    java_findings = java_parser.parse_directory(FIXTURES / "java")
    xslt_findings = xslt_parser.parse_directory(FIXTURES / "xslt")
    lineage = stitcher.stitch(java_findings, xslt_findings)

    assert len(lineage.nodes) > 0
    assert len(lineage.edges) > 0

    derived_from = [e for e in lineage.edges if e.edge_type.value == "DERIVED_FROM"]
    cross_lang = [e for e in derived_from if "xslt::" in e.source_id and "java::" in e.target_id]
    assert len(cross_lang) > 0


def test_multi_repo_stitching():
    """Multi-repo: lib-common constants should link to app-trade usage and XSLT fields."""
    lib_java = JavaParser(repo_name="lib-common")
    app_java = JavaParser(repo_name="app-trade")
    app_xslt = XsltParser(repo_name="app-trade")
    stitcher = Stitcher()

    java_findings = (
        lib_java.parse_directory(MULTI_REPO / "lib-common" / "java")
        + app_java.parse_directory(MULTI_REPO / "app-trade" / "java")
    )
    xslt_findings = app_xslt.parse_directory(MULTI_REPO / "app-trade" / "xslt")

    lineage = stitcher.stitch(java_findings, xslt_findings)

    assert len(lineage.nodes) > 0
    assert len(lineage.edges) > 0

    # Check cross-repo edges exist (lib-common <-> app-trade)
    cross_repo = [e for e in lineage.edges if e.edge_type.value == "CROSS_REPO"]
    assert len(cross_repo) > 0, (
        f"Should have CROSS_REPO edges between lib-common and app-trade, "
        f"got 0. Total edges: {len(lineage.edges)}"
    )

    # Check XSLT fields link to Java constants/fields
    xslt_to_java = [
        e for e in lineage.edges
        if "xslt::" in e.source_id and "java::" in e.target_id
    ]
    assert len(xslt_to_java) > 0, "XSLT fields should link to Java nodes"

    # Print the cross-repo links for visibility
    print(f"\n    Cross-repo edges: {len(cross_repo)}")
    for e in cross_repo[:5]:
        print(f"      {e.source_id} -> {e.target_id}")


def test_pyvis_output(tmp_path):
    java_parser = JavaParser()
    xslt_parser = XsltParser()
    stitcher = Stitcher()

    java_findings = java_parser.parse_directory(FIXTURES / "java")
    xslt_findings = xslt_parser.parse_directory(FIXTURES / "xslt")
    lineage = stitcher.stitch(java_findings, xslt_findings)

    provider = PyVisGraphProvider(output_dir=tmp_path)
    provider.ingest_lineage(lineage)
    provider.persist()

    assert (tmp_path / "lineage_graph.json").exists()
    assert (tmp_path / "lineage_graph.html").exists()

    data = json.loads((tmp_path / "lineage_graph.json").read_text())
    assert "nodes" in data
    assert "links" in data
    assert data["directed"] is True

    html = (tmp_path / "lineage_graph.html").read_text()
    assert "synapse-panel" in html
    assert "search-input" in html
    assert "JAVA_CONSTANT" in html
    assert "CROSS_REPO" in html


def test_multi_repo_pyvis_output(tmp_path):
    """Full pipeline: multi-repo -> stitch -> HTML with cross-repo links."""
    lib_java = JavaParser(repo_name="lib-common")
    app_java = JavaParser(repo_name="app-trade")
    app_xslt = XsltParser(repo_name="app-trade")
    stitcher = Stitcher()

    java_findings = (
        lib_java.parse_directory(MULTI_REPO / "lib-common" / "java")
        + app_java.parse_directory(MULTI_REPO / "app-trade" / "java")
    )
    xslt_findings = app_xslt.parse_directory(MULTI_REPO / "app-trade" / "xslt")

    lineage = stitcher.stitch(java_findings, xslt_findings)

    provider = PyVisGraphProvider(output_dir=tmp_path)
    provider.ingest_lineage(lineage)
    provider.persist()

    data = json.loads((tmp_path / "lineage_graph.json").read_text())

    # Verify repo tags on nodes
    nodes_with_repo = [n for n in data["nodes"] if n.get("repo")]
    assert len(nodes_with_repo) > 0, "Nodes should have repo property"

    repos_present = {n.get("repo") for n in data["nodes"] if n.get("repo")}
    assert "lib-common" in repos_present or "app-trade" in repos_present


# ---- Scanner tests ----

def test_scanner_discovers_files():
    """ModuleScanner should find all Java and XSLT files in a mixed module."""
    scanner = ModuleScanner()
    module = scanner.scan(MIXED_MODULE)

    assert len(module.java_files) == 1, f"Expected 1 java file, got {len(module.java_files)}"
    assert len(module.xslt_files) == 2, f"Expected 2 xslt files, got {len(module.xslt_files)}"
    assert module.name == "mixed-module"


def test_scanner_detects_xslt_refs():
    """Scanner should detect cross-language XSLT references in Java code."""
    scanner = ModuleScanner()
    module = scanner.scan(MIXED_MODULE)

    assert len(module.xslt_refs) >= 4, (
        f"Expected >= 4 cross-language refs, got {len(module.xslt_refs)}"
    )

    # Should find stream_source and string_path ref types
    ref_types = {r.ref_type for r in module.xslt_refs}
    assert "stream_source" in ref_types, f"Missing stream_source refs, got {ref_types}"
    assert "string_path" in ref_types, f"Missing string_path refs, got {ref_types}"


def test_scanner_resolves_xslt_paths():
    """Scanner should resolve XSLT filenames to actual file paths."""
    scanner = ModuleScanner()
    module = scanner.scan(MIXED_MODULE)

    resolved = [r for r in module.xslt_refs if r.xslt_resolved is not None]
    assert len(resolved) == len(module.xslt_refs), (
        f"All refs should resolve; unresolved: "
        f"{[r.xslt_filename for r in module.xslt_refs if r.xslt_resolved is None]}"
    )

    # Resolved paths should actually exist on disk
    for r in resolved:
        assert r.xslt_resolved.exists(), f"Resolved path doesn't exist: {r.xslt_resolved}"

    # Should resolve to the two known XSLT files
    resolved_names = {r.xslt_resolved.name for r in resolved}
    assert "trade_output.xsl" in resolved_names
    assert "settlement_mapping.xsl" in resolved_names


def test_auto_scan_full_pipeline(tmp_path):
    """End-to-end: auto-scan a mixed module, stitch, and persist to PyVis."""
    scanner = ModuleScanner()
    module = scanner.scan(MIXED_MODULE, name="mixed")

    java_parser = JavaParser(repo_name="mixed")
    xslt_parser = XsltParser(repo_name="mixed")
    stitcher = Stitcher()

    java_findings = []
    for jf in module.java_files:
        java_findings.extend(java_parser.parse_file(jf))

    xslt_findings = []
    for xf in module.xslt_files:
        xslt_findings.extend(xslt_parser.parse_file(xf))

    assert len(java_findings) > 0, "Should have Java findings"
    assert len(xslt_findings) > 0, "Should have XSLT findings"

    lineage = stitcher.stitch(java_findings, xslt_findings)

    assert len(lineage.nodes) > 0
    assert len(lineage.edges) > 0

    # Should have LOADS_XSLT edges from Java→XSLT references
    loads_xslt = [e for e in lineage.edges if e.edge_type.value == "LOADS_XSLT"]
    assert len(loads_xslt) > 0, "Should have LOADS_XSLT edges"

    # Persist and verify output
    provider = PyVisGraphProvider(output_dir=tmp_path)
    provider.ingest_lineage(lineage)
    provider.persist()

    assert (tmp_path / "lineage_graph.html").exists()
    assert (tmp_path / "lineage_graph.json").exists()

    data = json.loads((tmp_path / "lineage_graph.json").read_text())
    assert len(data["nodes"]) == len(lineage.nodes)
    assert len(data["links"]) == len(lineage.edges)

    # Per-field pages should be generated
    assert (tmp_path / "fields" / "index.html").exists()

    # Verify XSLT_FILE nodes are present (stored as "type" in JSON)
    xslt_file_nodes = [n for n in data["nodes"] if n.get("type") == "XSLT_FILE"]
    assert len(xslt_file_nodes) > 0, "Should have XSLT_FILE nodes"

    print(f"\n    Auto-scan pipeline: {len(lineage.nodes)} nodes, {len(lineage.edges)} edges")
    print(f"    LOADS_XSLT edges: {len(loads_xslt)}")
    print(f"    XSLT_FILE nodes: {len(xslt_file_nodes)}")


# ---- Multi-project / multi-module tests ----

def test_discover_modules():
    """ModuleScanner should detect sub-modules via pom.xml / src/ layout."""
    scanner = ModuleScanner()

    # project-alpha has two sub-modules: trade-service and common-lib (both have pom.xml)
    modules = scanner.discover_modules(MULTI_PROJECT / "project-alpha")
    module_names = [m.name for m in modules]
    assert "trade-service" in module_names, f"Missing trade-service, got {module_names}"
    assert "common-lib" in module_names, f"Missing common-lib, got {module_names}"

    # project-beta has one sub-module: settlement-module
    modules_beta = scanner.discover_modules(MULTI_PROJECT / "project-beta")
    module_names_beta = [m.name for m in modules_beta]
    assert "settlement-module" in module_names_beta, f"Missing settlement-module, got {module_names_beta}"


def test_scan_project():
    """scan_project should discover modules and scan each one."""
    scanner = ModuleScanner()
    project = scanner.scan_project(MULTI_PROJECT / "project-alpha", name="alpha")

    assert len(project.modules) >= 2, f"Expected >= 2 modules, got {len(project.modules)}"
    assert project.total_java >= 2, f"Expected >= 2 java files, got {project.total_java}"
    assert project.total_xslt >= 1, f"Expected >= 1 xslt file, got {project.total_xslt}"

    # trade-service module should have both Java and XSLT
    trade_mod = [m for m in project.modules if "trade-service" in m.name]
    assert len(trade_mod) == 1, f"Expected trade-service module, got {[m.name for m in project.modules]}"
    assert len(trade_mod[0].java_files) >= 1
    assert len(trade_mod[0].xslt_files) >= 1
    assert len(trade_mod[0].xslt_refs) >= 1, "trade-service should have XSLT refs"

    # common-lib module should have only Java
    lib_mod = [m for m in project.modules if "common-lib" in m.name]
    assert len(lib_mod) == 1
    assert len(lib_mod[0].java_files) >= 1
    assert len(lib_mod[0].xslt_files) == 0


def test_multi_project_full_pipeline(tmp_path):
    """End-to-end: two projects, each with modules, stitched into one graph."""
    from orchestrator.parser import SynapseConfig, SynapseTracer

    config = SynapseConfig(
        repos=[
            RepoConfig(
                name="alpha",
                path=MULTI_PROJECT / "project-alpha",
                project_scan=True,
            ),
            RepoConfig(
                name="beta",
                path=MULTI_PROJECT / "project-beta",
                project_scan=True,
            ),
        ],
        target_storages=["pyvis"],
        output_dir=tmp_path,
    )

    tracer = SynapseTracer(config)
    lineage = tracer.trace()

    assert len(lineage.nodes) > 0, "Should have nodes"
    assert len(lineage.edges) > 0, "Should have edges"

    # Should have LOADS_XSLT edges (Java loading XSLT)
    loads_xslt = [e for e in lineage.edges if e.edge_type.value == "LOADS_XSLT"]
    assert len(loads_xslt) > 0, "Should have LOADS_XSLT edges"

    # Should have cross-repo links (alpha constants <-> beta string literals)
    cross_repo = [e for e in lineage.edges if e.edge_type.value == "CROSS_REPO"]
    assert len(cross_repo) > 0, (
        f"Should have CROSS_REPO edges linking alpha and beta, got 0. "
        f"Total edges: {len(lineage.edges)}"
    )

    # Output files should exist
    assert (tmp_path / "lineage_graph.html").exists()
    assert (tmp_path / "lineage_graph.json").exists()
    assert (tmp_path / "fields" / "index.html").exists()

    data = json.loads((tmp_path / "lineage_graph.json").read_text())

    # Nodes should come from multiple module-qualified repos
    repos_in_graph = {n.get("repo") for n in data["nodes"] if n.get("repo")}
    assert len(repos_in_graph) >= 2, f"Expected nodes from >= 2 repos, got {repos_in_graph}"

    print(f"\n    Multi-project pipeline: {len(lineage.nodes)} nodes, {len(lineage.edges)} edges")
    print(f"    LOADS_XSLT: {len(loads_xslt)}, CROSS_REPO: {len(cross_repo)}")
    print(f"    Repos in graph: {repos_in_graph}")


# ---- trace_project: main + library dependency resolution ----

def test_trace_project_resolves_libs():
    """trace_project should scan main, find unresolved refs, then search libs."""
    result = trace_project(
        main=APP_WITH_LIBS / "main-app",
        libs=[APP_WITH_LIBS / "lib-fields", APP_WITH_LIBS / "lib-transform"],
    )

    # Should resolve MessageKey and TransformHelper from libraries
    assert "MessageKey" in result.resolved_from_libs, (
        f"Should resolve MessageKey, resolved: {result.resolved_from_libs}"
    )
    assert "TransformHelper" in result.resolved_from_libs
    assert result.resolved_from_libs["MessageKey"] == "lib-fields"
    assert result.resolved_from_libs["TransformHelper"] == "lib-transform"
    assert len(result.unresolved_classes) == 0, f"Nothing should be unresolved: {result.unresolved_classes}"

    # Graph should have nodes from both main and library
    assert result.node_count > 0
    assert result.edge_count > 0

    # Cross-repo edges should link main -> lib
    cross = result.edges_by_type("CROSS_REPO")
    assert len(cross) > 0, "Should have CROSS_REPO edges between main and libs"

    # LOADS_XSLT edges from Java -> XSLT within main
    loads = result.edges_by_type("LOADS_XSLT")
    assert len(loads) > 0, "Should have LOADS_XSLT edges"


def test_trace_project_without_libs():
    """trace_project without libs should still work, just with unresolved refs."""
    result = trace_project(main=APP_WITH_LIBS / "main-app")

    assert result.node_count > 0
    assert "MessageKey" in result.unresolved_classes
    assert "TransformHelper" in result.unresolved_classes
    assert len(result.resolved_from_libs) == 0


def test_parser_registry():
    """Parser registry should have built-in Java and XSLT parsers."""
    exts = supported_extensions()
    assert ".java" in exts
    assert ".xsl" in exts
    assert ".xslt" in exts


def test_trace_files_auto_dispatch():
    """trace_files should auto-dispatch to correct parser by file extension."""
    result = trace_files(
        java_files=[APP_WITH_LIBS / "main-app" / "trade-module" / "src" / "main" / "java" / "TradeService.java"],
        xslt_files=[APP_WITH_LIBS / "main-app" / "trade-module" / "src" / "main" / "resources" / "xslt" / "trade_mapping.xsl"],
    )
    assert result.node_count > 0
    assert len(result.java_findings) > 0
    assert len(result.xslt_findings) > 0


# ---- trace() with type/search_type ----

def test_trace_variable_like():
    """trace() should find a variable with fuzzy matching and drill into libs."""
    r = trace("N_EFFECTIVE_DATE", type="variable",
              project=APP_WITH_LIBS / "main-app",
              libs=[APP_WITH_LIBS / "lib-fields"])
    assert r.node_count > 0
    # Should find the constant in main and the literal in lib
    const_nodes = r.nodes_by_type("JAVA_CONSTANT")
    assert any("N_EFFECTIVE_DATE" in n.id for n in const_nodes), (
        f"Should find N_EFFECTIVE_DATE constant, got {[n.id for n in const_nodes]}"
    )
    # Should have cross-repo link to lib
    cross = r.edges_by_type("CROSS_REPO")
    assert len(cross) > 0, "Should drill into lib-fields"


def test_trace_variable_exact():
    """trace() with search_type='exact' should match strictly."""
    r = trace("N_EFFECTIVE_DATE", type="variable", search_type="exact",
              project=APP_WITH_LIBS / "main-app",
              libs=[APP_WITH_LIBS / "lib-fields"])
    assert r.node_count > 0


def test_trace_method():
    """trace() should isolate a single method's lineage."""
    r = trace("processIncoming", type="method", search_type="exact",
              project=APP_WITH_LIBS / "main-app")
    assert r.node_count > 0
    # The seed should be the method node
    method_nodes = r.nodes_by_type("JAVA_METHOD")
    assert any("processIncoming" in n.id for n in method_nodes)


def test_trace_class():
    """trace() should isolate a class and its connected graph."""
    r = trace("TradeService", type="class",
              project=APP_WITH_LIBS / "main-app")
    assert r.node_count > 0
    class_nodes = r.nodes_by_type("JAVA_CLASS")
    assert any("TradeService" in n.id for n in class_nodes)


def test_trace_fuzzy_like():
    """trace() with like search should match canonical field variations."""
    r = trace("effective_date", type="variable", search_type="like",
              project=APP_WITH_LIBS / "main-app",
              libs=[APP_WITH_LIBS / "lib-fields"])
    assert r.node_count > 0
    # Should find N_EFFECTIVE_DATE via fuzzy matching (effective_date -> n_effective_date)
    all_labels = [n.label for n in r.nodes]
    assert any("EFFECTIVE_DATE" in lbl.upper() for lbl in all_labels), (
        f"Fuzzy match should find EFFECTIVE_DATE, got labels: {all_labels}"
    )


def test_trace_result_filter():
    """TraceResult.filter() should post-filter an existing result."""
    full = trace_project(
        main=APP_WITH_LIBS / "main-app",
        libs=[APP_WITH_LIBS / "lib-fields"],
    )
    subset = full.filter("N_TRADE_ID")
    assert subset.node_count < full.node_count, "Filtered should have fewer nodes"
    assert subset.node_count > 0
    # Should contain nodes related to N_TRADE_ID
    assert any("TRADE_ID" in n.id.upper() for n in subset.nodes)


if __name__ == "__main__":
    print("Running smoke tests...")

    test_build_match_keys()
    print("  Field match keys: PASS")

    test_java_parser()
    print("  Java parser: PASS")

    test_java_parser_constants()
    print("  Java constants/literals: PASS")

    test_xslt_parser()
    print("  XSLT parser: PASS")

    test_stitcher_single_repo()
    print("  Stitcher (single-repo): PASS")

    test_multi_repo_stitching()
    print("  Multi-repo stitching: PASS")

    with tempfile.TemporaryDirectory() as td:
        test_pyvis_output(Path(td))
    print("  PyVis output: PASS")

    with tempfile.TemporaryDirectory() as td:
        test_multi_repo_pyvis_output(Path(td))
    print("  Multi-repo PyVis output: PASS")

    test_scanner_discovers_files()
    print("  Scanner discovers files: PASS")

    test_scanner_detects_xslt_refs()
    print("  Scanner detects XSLT refs: PASS")

    test_scanner_resolves_xslt_paths()
    print("  Scanner resolves XSLT paths: PASS")

    with tempfile.TemporaryDirectory() as td:
        test_auto_scan_full_pipeline(Path(td))
    print("  Auto-scan full pipeline: PASS")

    test_discover_modules()
    print("  Discover modules: PASS")

    test_scan_project()
    print("  Scan project: PASS")

    with tempfile.TemporaryDirectory() as td:
        test_multi_project_full_pipeline(Path(td))
    print("  Multi-project full pipeline: PASS")

    test_trace_project_resolves_libs()
    print("  trace_project resolves libs: PASS")

    test_trace_project_without_libs()
    print("  trace_project without libs: PASS")

    test_parser_registry()
    print("  Parser registry: PASS")

    test_trace_files_auto_dispatch()
    print("  trace_files auto dispatch: PASS")

    test_trace_variable_like()
    print("  trace variable (like): PASS")

    test_trace_variable_exact()
    print("  trace variable (exact): PASS")

    test_trace_method()
    print("  trace method: PASS")

    test_trace_class()
    print("  trace class: PASS")

    test_trace_fuzzy_like()
    print("  trace fuzzy like: PASS")

    test_trace_result_filter()
    print("  TraceResult.filter(): PASS")

    print("\nAll smoke tests passed!")
