"""Smoke tests: single-repo, multi-repo, and field variation matching."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestrator.models import RepoConfig
from orchestrator.parsers.java_parser import JavaParser
from orchestrator.parsers.xslt_parser import XsltParser
from orchestrator.stitcher import Stitcher, _build_match_keys
from orchestrator.storage.local_graph_pyvis import PyVisGraphProvider

FIXTURES = Path(__file__).parent / "fixtures" / "sample"
MULTI_REPO = Path(__file__).parent / "fixtures" / "multi-repo"


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

    print("\nAll smoke tests passed!")
