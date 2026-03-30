"""Generates an HTML report from a trace result."""
from __future__ import annotations
import html
from typing import List, TYPE_CHECKING
from modules.trace_core.models.trace_models import TraceNode, TraceSummary, BranchPath

if TYPE_CHECKING:
    pass

_TYPE_COLORS = {
    "EXTRACTION": "#3B82F6",
    "MAPPING": "#8B5CF6",
    "ENRICHMENT": "#10B981",
    "OVERRIDE": "#F59E0B",
    "DEFAULTING": "#6B7280",
    "PASS_THROUGH": "#94A3B8",
    "CONDITIONAL_ASSIGNMENT": "#EAB308",
    "FINAL_REPORT_ASSIGNMENT": "#EF4444",
}


class HtmlExporter:
    """Renders a trace result as a self-contained HTML page."""

    def export(self, summary: TraceSummary, nodes: List[TraceNode], branches: List[BranchPath]) -> str:
        steps_html = self._render_pipeline(nodes)
        branches_html = self._render_branches(branches)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Lineage Trace: {html.escape(summary.field_name)}</title>
<style>
  body {{ font-family: 'JetBrains Mono', monospace; background:#0f172a; color:#e2e8f0; padding:2rem; }}
  h1 {{ color:#38bdf8; }} h2 {{ color:#7dd3fc; border-bottom:1px solid #334155; padding-bottom:0.5rem; }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600; margin-left:8px; }}
  .card {{ background:#1e293b; border:1px solid #334155; border-radius:8px; padding:1rem; margin:0.5rem 0; }}
  .node {{ border-left:4px solid; padding:0.75rem; margin:0.5rem 0; border-radius:4px; background:#1e293b; }}
  .evidence {{ font-size:0.8rem; color:#94a3b8; margin-top:0.5rem; }}
  .branch {{ background:#1e293b; border:1px solid #475569; border-radius:8px; padding:1rem; margin:0.5rem 0; }}
  pre {{ background:#0f172a; padding:0.5rem; border-radius:4px; overflow-x:auto; font-size:0.75rem; color:#a3e635; }}
  .pipeline {{ display:flex; flex-wrap:wrap; gap:0.5rem; align-items:center; }}
  .arrow {{ color:#475569; font-size:1.2rem; }}
</style>
</head>
<body>
<h1>Field Lineage: {html.escape(summary.field_name)}</h1>
<div class="card">
  <b>Origin:</b> <span class="badge" style="background:#0284c7">{html.escape(summary.origin.value)}</span>
  &nbsp;<b>Nodes:</b> {summary.total_nodes}
  &nbsp;<b>Branches:</b> {summary.branch_count}
  &nbsp;<b>XSLT:</b> {'Yes' if summary.has_xslt else 'No'}
  &nbsp;<b>Java:</b> {'Yes' if summary.has_java else 'No'}
</div>
<h2>Technical Explanation</h2>
<div class="card"><pre>{html.escape(summary.technical_explanation)}</pre></div>
<h2>Business Explanation</h2>
<div class="card">{html.escape(summary.business_explanation)}</div>
<h2>Pipeline ({len(nodes)} steps)</h2>
{steps_html}
<h2>Branches ({len(branches)})</h2>
{branches_html}
</body></html>"""

    def _render_pipeline(self, nodes: List[TraceNode]) -> str:
        parts = []
        for node in nodes:
            t = node.transformation_type.value if node.transformation_type else "UNKNOWN"
            color = _TYPE_COLORS.get(t, "#6B7280")
            ev = node.evidence
            ev_parts = []
            if ev.class_or_template:
                ev_parts.append(f"Class: {html.escape(ev.class_or_template)}")
            if ev.method_or_template_name:
                ev_parts.append(f"Method: {html.escape(ev.method_or_template_name)}")
            if ev.file_path:
                ev_parts.append(f"File: {html.escape(ev.file_path)}")
            if ev.line_number:
                ev_parts.append(f"Line: {ev.line_number}")
            code_html = ""
            if ev.raw_code:
                code_html = f"<pre>{html.escape(ev.raw_code[:200])}</pre>"
            parts.append(f"""
<div class="node" style="border-color:{color}">
  <b>{html.escape(node.label)}</b>
  <span class="badge" style="background:{color}">{html.escape(t)}</span>
  <div class="evidence">{' | '.join(ev_parts)}</div>
  {code_html}
</div>""")
        return "\n".join(parts)

    def _render_branches(self, branches: List[BranchPath]) -> str:
        parts = []
        for b in branches:
            outcome = html.escape(b.outcome or "")
            parts.append(f"""
<div class="branch">
  <b>Condition:</b> {html.escape(b.condition)}<br/>
  <b>Outcome:</b> {outcome}
</div>""")
        return "\n".join(parts)
