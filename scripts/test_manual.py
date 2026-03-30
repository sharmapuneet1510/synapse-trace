#!/usr/bin/env python3
"""
Manual test script – fully self-contained.
No config files, no external repos needed.
All sample Java and XSLT source is embedded inline.

Run:
    python3 scripts/test_manual.py
"""
import sys
import os
import uuid
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ─────────────────────────────────────────────────
# 1.  EMBEDDED SAMPLE SOURCE CODE
# ─────────────────────────────────────────────────

SAMPLE_XSLT = """\
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- Entry template: builds the clearing report -->
  <xsl:template name="buildClearingReport">
    <xsl:variable name="tradeId"     select="//trade/id"/>
    <xsl:variable name="clearFlag"   select="//trade/cleared"/>
    <xsl:variable name="jurisdiction" select="//trade/jurisdiction"/>

    <xsl:call-template name="setClearedField">
      <xsl:with-param name="flag"   select="$clearFlag"/>
      <xsl:with-param name="jur"    select="$jurisdiction"/>
    </xsl:call-template>
  </xsl:template>

  <!-- Sets the N_CLEARED output field with conditional logic -->
  <xsl:template name="setClearedField">
    <xsl:param name="flag"/>
    <xsl:param name="jur"/>

    <xsl:choose>
      <xsl:when test="$flag = 'true'">
        <N_CLEARED>Y</N_CLEARED>
      </xsl:when>
      <xsl:when test="$jur = 'JP'">
        <N_CLEARED>N</N_CLEARED>
      </xsl:when>
      <xsl:otherwise>
        <N_CLEARED>UNKNOWN</N_CLEARED>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Maps N_SETTLEMENT_DATE from source -->
  <xsl:template name="buildSettlementDate">
    <xsl:variable name="rawDate" select="//trade/settlementDate"/>
    <N_SETTLEMENT_DATE><xsl:value-of select="$rawDate"/></N_SETTLEMENT_DATE>
  </xsl:template>

  <!-- Maps N_TRADE_AMOUNT -->
  <xsl:template name="buildTradeAmount">
    <xsl:variable name="amount" select="//trade/notionalAmount"/>
    <N_TRADE_AMOUNT><xsl:value-of select="$amount"/></N_TRADE_AMOUNT>
  </xsl:template>

</xsl:stylesheet>
"""

SAMPLE_JAVA_CLEARING = """\
package com.xxx.clearing;

import com.xxx.model.Trade;
import com.xxx.model.ClearingReport;
import com.xxx.helper.ClearingHelper;

/**
 * ClearingService enriches the clearing report from the XSLT pre-processed trade.
 */
public class ClearingService {

    private ClearingHelper helper = new ClearingHelper();

    public ClearingReport process(Trade trade) {
        ClearingReport report = new ClearingReport();

        // Enrich N_CLEARED using business logic
        String cleared = helper.getClearedFlag(trade);
        report.setNCleared(cleared);

        // Set N_SETTLEMENT_DATE
        report.setNSettlementDate(trade.getSettlementDate());

        return report;
    }

    public void applyJurisdictionOverride(ClearingReport report, String jurisdiction) {
        if ("JP".equals(jurisdiction)) {
            report.setNCleared("N");
        } else if ("US".equals(jurisdiction)) {
            String existing = report.getNCleared();
            if (existing == null || existing.isEmpty()) {
                report.setNCleared("Y");
            }
        }
    }
}
"""

SAMPLE_JAVA_HELPER = """\
package com.xxx.helper;

import com.xxx.model.Trade;
import com.xxx.rules.ClearingRulesEngine;

public class ClearingHelper {

    private ClearingRulesEngine rulesEngine = new ClearingRulesEngine();

    public String getClearedFlag(Trade trade) {
        if (trade == null) {
            return "UNKNOWN";
        }
        if (trade.isCleared()) {
            return "Y";
        } else if ("JP".equals(trade.getJurisdiction())) {
            return "N";
        } else {
            return rulesEngine.applyOverride(trade, "DEFAULT");
        }
    }

    public String resolveStatus(Trade trade) {
        String status = trade.getStatus();
        if ("CONFIRMED".equals(status)) {
            return "Y";
        }
        return "N";
    }
}
"""

SAMPLE_JAVA_RULES = """\
package com.xxx.rules;

import com.xxx.model.Trade;

public class ClearingRulesEngine {

    public String applyOverride(Trade trade, String defaultValue) {
        if (trade.isMandatoryClearing()) {
            return "Y";
        }
        return defaultValue;
    }
}
"""

SAMPLE_JAVA_REPORT = """\
package com.xxx.model;

public class ClearingReport {

    private String nCleared;
    private String nSettlementDate;
    private String nTradeAmount;
    private String nTradeId;

    public String getNCleared() { return nCleared; }
    public void setNCleared(String nCleared) { this.nCleared = nCleared; }

    public String getNSettlementDate() { return nSettlementDate; }
    public void setNSettlementDate(String nSettlementDate) { this.nSettlementDate = nSettlementDate; }

    public String getNTradeAmount() { return nTradeAmount; }
    public void setNTradeAmount(String nTradeAmount) { this.nTradeAmount = nTradeAmount; }

    public String getNTradeId() { return nTradeId; }
    public void setNTradeId(String nTradeId) { this.nTradeId = nTradeId; }
}
"""

# ─────────────────────────────────────────────────
# 2.  WRITE TEMP FILES
# ─────────────────────────────────────────────────

def setup_temp_repo():
    tmpdir = tempfile.mkdtemp(prefix="synapse_trace_test_")

    xslt_dir = os.path.join(tmpdir, "src", "main", "resources", "xslt")
    java_dirs = {
        "clearing": os.path.join(tmpdir, "src", "main", "java", "com", "xxx", "clearing"),
        "helper":   os.path.join(tmpdir, "src", "main", "java", "com", "xxx", "helper"),
        "rules":    os.path.join(tmpdir, "src", "main", "java", "com", "xxx", "rules"),
        "model":    os.path.join(tmpdir, "src", "main", "java", "com", "xxx", "model"),
    }

    os.makedirs(xslt_dir, exist_ok=True)
    for d in java_dirs.values():
        os.makedirs(d, exist_ok=True)

    # Write XSLT
    with open(os.path.join(xslt_dir, "clearing_transform.xsl"), "w") as f:
        f.write(SAMPLE_XSLT)

    # Write Java files
    with open(os.path.join(java_dirs["clearing"], "ClearingService.java"), "w") as f:
        f.write(SAMPLE_JAVA_CLEARING)
    with open(os.path.join(java_dirs["helper"], "ClearingHelper.java"), "w") as f:
        f.write(SAMPLE_JAVA_HELPER)
    with open(os.path.join(java_dirs["rules"], "ClearingRulesEngine.java"), "w") as f:
        f.write(SAMPLE_JAVA_RULES)
    with open(os.path.join(java_dirs["model"], "ClearingReport.java"), "w") as f:
        f.write(SAMPLE_JAVA_REPORT)

    return tmpdir


# ─────────────────────────────────────────────────
# 3.  INLINE TRACE CONFIG (no yaml files needed)
# ─────────────────────────────────────────────────

TRACE_CONFIG = {
    "trace": {
        "includePackages": ["*xxx*", "com.xxx.*"],
        "excludePackages": ["java.*", "javax.*", "org.springframework.*"],
        "stopPackages": ["org.apache.*"],
        "maxDepth": 10,
        "followInternalCallsOnly": True,
        "enableConditionTracing": True,
        "enableXsltImports": True,
    }
}


# ─────────────────────────────────────────────────
# 4.  RUN TRACE DIRECTLY (bypass config files)
# ─────────────────────────────────────────────────

def run_trace(field_name: str, repo_path: str):
    from modules.trace_core.indexers.repo_indexer import RepoIndexer
    from modules.trace_core.tracing.trace_context import TraceContext
    from modules.trace_core.tracing.field_trace_engine import FieldTraceEngine
    from modules.trace_core.tracing.branch_trace_engine import BranchTraceEngine
    from modules.trace_core.graph.nx_graph_builder import NxGraphBuilder
    from modules.trace_core.exporters.trace_result import TraceResult
    from modules.trace_core.explain.trace_summarizer import TraceSummarizer

    trace_id = str(uuid.uuid4())

    # Index the temp repo
    indexer = RepoIndexer()
    index = indexer.index([repo_path], field_name=field_name)

    ctx = TraceContext(
        trace_id=trace_id,
        field_name=field_name,
        config=TRACE_CONFIG,
        max_depth=10,
        enable_condition_tracing=True,
        enable_xslt_imports=True,
    )

    engine        = FieldTraceEngine(index, TRACE_CONFIG)
    branch_engine = BranchTraceEngine()
    graph_builder = NxGraphBuilder()
    summarizer    = TraceSummarizer()

    nodes, edges, origin = engine.trace(field_name, ctx)
    branches = branch_engine.build_branches(nodes, edges, ctx)
    graph    = graph_builder.build(nodes, edges)
    summary  = summarizer.summarize(field_name, origin, nodes, edges, branches)

    return TraceResult(
        field_name=field_name,
        trace_id=trace_id,
        summary=summary,
        graph=graph,
        nodes=nodes,
        edges=edges,
        branches=branches,
        metadata={"origin": origin.value},
        evidence_list=[n.evidence for n in nodes],
    )


# ─────────────────────────────────────────────────
# 5.  PRINT HELPERS
# ─────────────────────────────────────────────────

SEP  = "─" * 60
SEP2 = "═" * 60

def section(title):
    print(f"\n{SEP2}")
    print(f"  {title}")
    print(SEP2)

def subsection(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ─────────────────────────────────────────────────
# 6.  MAIN
# ─────────────────────────────────────────────────

def main():
    print(SEP2)
    print("  SynapseTrace – Manual Self-Contained Test")
    print(SEP2)

    # Setup
    print("\n[1/3] Writing sample source files to temp directory...")
    repo_path = setup_temp_repo()
    print(f"      Temp repo: {repo_path}")

    fields_to_test = ["N_CLEARED", "N_SETTLEMENT_DATE"]

    try:
        for field_name in fields_to_test:
            section(f"TRACING FIELD: {field_name}")

            print(f"\n[2/3] Running trace for '{field_name}'...")
            result = run_trace(field_name, repo_path)

            # ── Summary ──────────────────────────────────────
            subsection("SUMMARY")
            print(f"  Trace ID    : {result.trace_id}")
            print(f"  Field       : {result.field_name}")
            print(f"  Origin      : {result.summary.origin.value}")
            print(f"  Total Nodes : {result.summary.total_nodes}")
            print(f"  Branches    : {result.summary.branch_count}")
            print(f"  Has XSLT    : {result.summary.has_xslt}")
            print(f"  Has Java    : {result.summary.has_java}")

            # ── Pipeline steps ────────────────────────────────
            subsection("PIPELINE STEPS")
            for i, step in enumerate(result.summary.pipeline_steps, 1):
                print(f"  {i:2}. {step}")

            # ── Nodes with evidence ───────────────────────────
            subsection("TRACE NODES (with evidence)")
            for node in result.nodes:
                ev = node.evidence
                print(f"\n  [{node.node_type.upper()}] {node.label}")
                print(f"    Transformation : {node.transformation_type.value if node.transformation_type else '—'}")
                if ev.file_path:
                    print(f"    File           : {ev.file_path}")
                if ev.class_or_template:
                    print(f"    Class/Template : {ev.class_or_template}")
                if ev.method_or_template_name:
                    print(f"    Method         : {ev.method_or_template_name}")
                if ev.line_number:
                    print(f"    Line           : {ev.line_number}")
                if ev.condition_text:
                    print(f"    Condition      : {ev.condition_text[:80]}")
                conds = node.metadata.get("conditions", [])
                if conds:
                    print(f"    Conditions detected:")
                    for c in conds[:3]:
                        print(f"      • [{c.get('branch_type','?')}] {c.get('condition_text','')[:60]}")

            # ── Branches ─────────────────────────────────────
            subsection("BRANCH PATHS")
            for b in result.branches:
                print(f"  Branch [{b.branch_id}]")
                print(f"    Condition : {b.condition}")
                print(f"    Outcome   : {b.outcome or '—'}")

            # ── Graph stats ───────────────────────────────────
            subsection("GRAPH (NetworkX MultiDiGraph)")
            G = result.to_graph()
            print(f"  Nodes : {G.number_of_nodes()}")
            print(f"  Edges : {G.number_of_edges()}")
            if G.number_of_nodes():
                print("  Node list:")
                for nid, attrs in list(G.nodes(data=True))[:5]:
                    print(f"    • {nid[:60]}  [{attrs.get('transformation_type','?')}]")
            if G.number_of_edges():
                print("  Edge list:")
                for u, v, d in list(G.edges(data=True))[:5]:
                    print(f"    • {u[:30]} --[{d.get('relation','?')}]--> {v[:30]}")

            # ── Pipeline JSON ─────────────────────────────────
            subsection("to_pipeline_json()")
            pj = result.to_pipeline_json()
            print(f"  total_steps : {pj.get('total_steps', 0)}")
            for s in pj.get("steps", [])[:3]:
                print(f"    Step {s['order']}: {s['label']}  [{s.get('transformation_type','?')}]")

            # ── Branch JSON ───────────────────────────────────
            subsection("to_branch_json()")
            bj = result.to_branch_json()
            print(f"  branch_count : {bj.get('branch_count', 0)}")
            for b in bj.get("branches", [])[:3]:
                print(f"    [{b['branch_id']}] {b['condition'][:60]}  → {b.get('outcome','?')}")

            # ── Neo4j export ──────────────────────────────────
            subsection("to_neo4j()")
            nj = result.to_neo4j()
            print(f"  Nodes         : {len(nj.get('nodes', []))}")
            print(f"  Relationships : {len(nj.get('relationships', []))}")
            print(f"  Cypher stmts  : {len(nj.get('cypher_statements', []))}")
            for stmt in nj.get("cypher_statements", [])[:2]:
                print(f"    {stmt[:90]}")

            # ── HTML export ───────────────────────────────────
            subsection("to_html()")
            html = result.to_html()
            out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "html")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{field_name}_test.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  HTML saved : {out_path}  ({len(html)} bytes)")

            # ── Business explanation ──────────────────────────
            subsection("BUSINESS EXPLANATION")
            print(f"  {result.summary.business_explanation}")

            # ── Technical explanation ─────────────────────────
            subsection("TECHNICAL EXPLANATION")
            print(result.summary.technical_explanation)

    finally:
        print(f"\n[3/3] Cleaning up temp repo: {repo_path}")
        shutil.rmtree(repo_path, ignore_errors=True)

    print(f"\n{SEP2}")
    print("  ALL TESTS COMPLETE")
    print(SEP2)


if __name__ == "__main__":
    main()
