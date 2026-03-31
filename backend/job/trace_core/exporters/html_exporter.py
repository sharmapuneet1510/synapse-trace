"""Generates a self-contained HTML report from a trace result.

The report includes:
  - Summary card (origin, node/branch counts)
  - Interactive vis.js network graph (rendered from the NetworkX DiGraph)
  - Pipeline steps (ordered node table)
  - Branch conditions
"""
from __future__ import annotations
import html
import json
from typing import List, Optional, TYPE_CHECKING

from trace_core.models.trace_models import TraceNode, TraceSummary, BranchPath

if TYPE_CHECKING:
    import networkx as nx

_TYPE_COLORS: dict[str, str] = {
    "EXTRACTION":              "#7c3aed",
    "MAPPING":                 "#0891b2",
    "ENRICHMENT":              "#059669",
    "OVERRIDE":                "#d97706",
    "DEFAULTING":              "#6b7280",
    "PASS_THROUGH":            "#9ca3af",
    "CONDITIONAL_ASSIGNMENT":  "#ea580c",
    "FINAL_REPORT_ASSIGNMENT": "#dc2626",
}

_TYPE_LABELS: dict[str, str] = {
    "EXTRACTION":              "EXTRACT",
    "MAPPING":                 "MAP",
    "ENRICHMENT":              "ENRICH",
    "OVERRIDE":                "OVERRIDE",
    "DEFAULTING":              "DEFAULT",
    "PASS_THROUGH":            "PASS",
    "CONDITIONAL_ASSIGNMENT":  "COND",
    "FINAL_REPORT_ASSIGNMENT": "FINAL",
}


def _nx_to_visjs(G: "nx.MultiDiGraph") -> dict:
    """Serialise a NetworkX MultiDiGraph to a vis.js-compatible dict.

    Returns
    -------
    {"nodes": [...], "edges": [...]}
    """
    vis_nodes = []
    vis_edges = []

    for node_id, data in G.nodes(data=True):
        ttype  = data.get("transformation_type") or ""
        label  = data.get("label") or node_id
        color  = _TYPE_COLORS.get(ttype, "#6b7280")
        badge  = _TYPE_LABELS.get(ttype, ttype or "—")
        ntype  = data.get("node_type") or ""

        # Multi-line label: name on first line, type badge on second
        short = label if len(label) <= 30 else label[:27] + "…"
        vis_label = f"{short}\n[{badge}]"

        vis_nodes.append({
            "id":    node_id,
            "label": vis_label,
            "title": f"<b>{html.escape(label)}</b><br/>{ntype} · {ttype}",
            "color": {
                "background": color + "22",   # 13 % opacity fill
                "border":     color,
                "highlight":  {"background": color + "44", "border": color},
                "hover":      {"background": color + "33", "border": color},
            },
            "font": {
                "color": "#111827",
                "size":  11,
                "face":  "IBM Plex Mono, monospace",
                "multi": "html",
            },
            "borderWidth":          2,
            "borderWidthSelected":  3,
            "shape":                "box",
            "margin":               8,
            "shadow":               {"enabled": True, "color": "rgba(0,0,0,0.08)", "size": 6},
        })

    edge_id = 0
    for src, tgt, data in G.edges(data=True):
        relation = data.get("relation") or data.get("label") or ""
        cond     = data.get("condition_text") or ""
        dashed   = relation in ("conditionally_feeds", "overrides", "triggers")
        title    = html.escape(relation)
        if cond:
            title += f"<br/><i>{html.escape(cond[:80])}</i>"

        vis_edges.append({
            "id":     edge_id,
            "from":   src,
            "to":     tgt,
            "label":  relation if relation not in ("feeds",) else "",
            "title":  title,
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.6}},
            "dashes": dashed,
            "color":  {"color": "#9ca3af", "highlight": "#6b7280", "hover": "#374151"},
            "width":  1.5,
            "font":   {"size": 9, "color": "#9ca3af", "face": "IBM Plex Mono, monospace", "align": "middle"},
            "smooth": {"type": "curvedCW", "roundness": 0.1},
        })
        edge_id += 1

    return {"nodes": vis_nodes, "edges": vis_edges}


class HtmlExporter:
    """Renders a trace result as a self-contained HTML page with an interactive graph."""

    def export(
        self,
        summary: TraceSummary,
        nodes: List[TraceNode],
        branches: List[BranchPath],
        graph: Optional["nx.MultiDiGraph"] = None,
    ) -> str:
        """Generate the full HTML document.

        Parameters
        ----------
        summary   : TraceSummary from the trace result.
        nodes     : Ordered list of TraceNode objects (pipeline steps).
        branches  : BranchPath list.
        graph     : NetworkX MultiDiGraph — when provided, an interactive
                    vis.js network is rendered at the top of the report.
        """
        graph_section = self._render_graph(graph, summary.field_name) if graph is not None else ""
        steps_html    = self._render_pipeline(nodes)
        branches_html = self._render_branches(branches)
        legend_html   = self._render_legend()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Lineage: {html.escape(summary.field_name)}</title>
<!-- vis-network (self-contained CDN) -->
<script src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script>
<link  href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Barlow+Condensed:wght@600;700&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'IBM Plex Mono', monospace;
    background: #f4f5f7;
    color: #111827;
    font-size: 13px;
    line-height: 1.55;
  }}
  .page {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}

  /* ── Header ── */
  .hdr {{
    display: flex; align-items: baseline; gap: 16px;
    border-bottom: 2px solid #dc2626;
    padding-bottom: 12px; margin-bottom: 24px;
  }}
  .hdr-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700; font-size: 26px; letter-spacing: 0.06em;
    color: #111827;
  }}
  .hdr-field {{ color: #dc2626; }}
  .badge {{
    display: inline-flex; align-items: center;
    padding: 2px 8px; border-radius: 3px;
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700; font-size: 11px; letter-spacing: 0.08em;
    text-transform: uppercase;
  }}

  /* ── Summary card ── */
  .summary-card {{
    background: #fff; border: 1px solid #e2e4e9;
    border-radius: 6px; padding: 16px 20px;
    display: flex; flex-wrap: wrap; gap: 24px;
    margin-bottom: 28px;
  }}
  .stat {{ display: flex; flex-direction: column; gap: 3px; }}
  .stat-label {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700; font-size: 10px; letter-spacing: 0.1em;
    color: #9ca3af; text-transform: uppercase;
  }}
  .stat-value {{ font-size: 15px; font-weight: 600; color: #111827; }}

  /* ── Section heading ── */
  h2 {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700; font-size: 15px; letter-spacing: 0.1em;
    text-transform: uppercase; color: #374151;
    border-left: 3px solid #dc2626; padding-left: 10px;
    margin: 28px 0 14px;
  }}

  /* ── Graph container ── */
  #lineage-graph {{
    width: 100%; height: 520px;
    background: #fff;
    border: 1px solid #e2e4e9;
    border-radius: 6px;
    overflow: hidden;
  }}

  /* ── Pipeline nodes ── */
  .node-card {{
    background: #fff; border: 1px solid #e2e4e9;
    border-left-width: 3px; border-radius: 5px;
    padding: 12px 14px; margin-bottom: 8px;
    transition: box-shadow 0.15s;
  }}
  .node-card:hover {{ box-shadow: 0 2px 10px rgba(0,0,0,0.07); }}
  .node-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
  .node-label {{ font-weight: 500; font-size: 12px; }}
  .evidence {{
    font-size: 11px; color: #6b7280; margin-top: 4px;
    display: flex; flex-wrap: wrap; gap: 12px;
  }}
  .ev-item {{ display: flex; gap: 4px; }}
  .ev-key {{ color: #9ca3af; }}
  pre {{
    background: #f0f1f3; border: 1px solid #e2e4e9;
    border-radius: 4px; padding: 8px 10px; margin-top: 8px;
    font-size: 11px; color: #059669;
    overflow-x: auto; white-space: pre-wrap; word-break: break-all;
  }}

  /* ── Branches ── */
  .branch-card {{
    background: #fff; border: 1px solid #e2e4e9;
    border-left: 3px solid #ea580c;
    border-radius: 5px; padding: 12px 14px; margin-bottom: 8px;
  }}
  .branch-cond {{ font-size: 12px; margin: 4px 0; }}
  .branch-outcome {{ font-size: 11px; color: #059669; margin-top: 6px; }}

  /* ── Legend ── */
  .legend {{
    display: flex; flex-wrap: wrap; gap: 10px;
    margin-bottom: 16px;
  }}
  .legend-item {{
    display: flex; align-items: center; gap: 6px;
    font-size: 10px; color: #6b7280;
  }}
  .legend-dot {{
    width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0;
  }}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="hdr">
    <span class="hdr-title">LINEAGE&nbsp;<span class="hdr-field">{html.escape(summary.field_name)}</span></span>
    <span class="badge" style="background:rgba(8,145,178,0.1);color:#0891b2;border:1px solid rgba(8,145,178,0.25)">
      {html.escape(summary.origin.value)}
    </span>
  </div>

  <!-- Summary -->
  <div class="summary-card">
    <div class="stat"><span class="stat-label">Nodes</span><span class="stat-value">{summary.total_nodes}</span></div>
    <div class="stat"><span class="stat-label">Branches</span><span class="stat-value">{summary.branch_count}</span></div>
    <div class="stat"><span class="stat-label">XSLT</span><span class="stat-value">{'Yes' if summary.has_xslt else 'No'}</span></div>
    <div class="stat"><span class="stat-label">Java</span><span class="stat-value">{'Yes' if summary.has_java else 'No'}</span></div>
  </div>

  <!-- Business explanation -->
  <h2>Business Context</h2>
  <div style="background:#fff;border:1px solid #e2e4e9;border-radius:5px;padding:14px 16px;line-height:1.65;font-size:12px;color:#374151;">
    {html.escape(summary.business_explanation or '—')}
  </div>

  <!-- Technical explanation -->
  <h2>Technical Summary</h2>
  <div style="background:#fff;border:1px solid #e2e4e9;border-radius:5px;padding:14px 16px;">
    <pre style="margin:0;background:transparent;border:none;padding:0;color:#374151;">{html.escape(summary.technical_explanation or '—')}</pre>
  </div>

  <!-- Interactive graph -->
  {graph_section}

  <!-- Pipeline -->
  <h2>Pipeline ({len(nodes)} steps)</h2>
  {legend_html}
  {steps_html}

  <!-- Branches -->
  <h2>Branches ({len(branches)})</h2>
  {branches_html}

</div>
</body>
</html>"""

    # ── Graph section ─────────────────────────────────────────────────────────

    def _render_graph(self, G: "nx.MultiDiGraph", field_name: str) -> str:
        """Render an interactive vis.js network from the NetworkX graph."""
        if G is None or G.number_of_nodes() == 0:
            return ""

        vis_data   = _nx_to_visjs(G)
        nodes_json = json.dumps(vis_data["nodes"], ensure_ascii=False)
        edges_json = json.dumps(vis_data["edges"], ensure_ascii=False)

        options_json = json.dumps({
            "layout": {
                "hierarchical": {
                    "enabled":       True,
                    "direction":     "LR",
                    "sortMethod":    "directed",
                    "levelSeparation": 200,
                    "nodeSpacing":     100,
                    "treeSpacing":     120,
                    "blockShifting":   True,
                    "edgeMinimization": True,
                }
            },
            "physics": {"enabled": False},
            "interaction": {
                "hover":         True,
                "tooltipDelay":  150,
                "navigationButtons": False,
                "keyboard":      False,
            },
            "edges": {"smooth": {"type": "cubicBezier", "forceDirection": "horizontal", "roundness": 0.4}},
            "nodes": {"widthConstraint": {"maximum": 180}},
        })

        return f"""
<h2>Lineage Graph — {html.escape(field_name)}</h2>
<div id="lineage-graph"></div>
<script>
(function() {{
  var container = document.getElementById('lineage-graph');
  var data = {{
    nodes: new vis.DataSet({nodes_json}),
    edges: new vis.DataSet({edges_json}),
  }};
  var options = {options_json};
  var network = new vis.Network(container, data, options);
  network.fit({{ animation: false }});
}})();
</script>"""

    # ── Pipeline steps ────────────────────────────────────────────────────────

    def _render_pipeline(self, nodes: List[TraceNode]) -> str:
        parts = []
        for node in nodes:
            t     = node.transformation_type.value if node.transformation_type else "UNKNOWN"
            color = _TYPE_COLORS.get(t, "#6b7280")
            badge = _TYPE_LABELS.get(t, t)
            ev    = node.evidence

            ev_items = []
            if ev.class_or_template:
                ev_items.append(("Class", html.escape(ev.class_or_template)))
            if ev.method_or_template_name:
                ev_items.append(("Method", html.escape(ev.method_or_template_name)))
            if ev.file_path:
                import os
                ev_items.append(("File", html.escape(os.path.basename(ev.file_path))))
            if ev.line_number:
                ev_items.append(("Line", str(ev.line_number)))
            if ev.condition_text:
                ev_items.append(("Condition", html.escape(ev.condition_text[:80])))

            ev_html = "".join(
                f'<span class="ev-item"><span class="ev-key">{k}:</span> {v}</span>'
                for k, v in ev_items
            )
            code_html = ""
            if ev.raw_code:
                code_html = f"<pre>{html.escape(ev.raw_code[:300])}</pre>"

            parts.append(f"""
<div class="node-card" style="border-left-color:{color}">
  <div class="node-header">
    <span class="node-label">{html.escape(node.label)}</span>
    <span class="badge" style="background:{color}22;color:{color};border:1px solid {color}44">{badge}</span>
  </div>
  <div class="evidence">{ev_html}</div>
  {code_html}
</div>""")
        return "\n".join(parts)

    # ── Branches ──────────────────────────────────────────────────────────────

    def _render_branches(self, branches: List[BranchPath]) -> str:
        if not branches:
            return '<p style="color:#9ca3af;font-size:12px;">No branches detected.</p>'
        parts = []
        for b in branches:
            outcome_html = ""
            if b.outcome:
                outcome_html = f'<div class="branch-outcome">→ {html.escape(b.outcome)}</div>'
            parts.append(f"""
<div class="branch-card">
  <span class="badge" style="background:rgba(234,88,12,0.08);color:#ea580c;border:1px solid rgba(234,88,12,0.2)">
    {html.escape(b.branch_id)}
  </span>
  <div class="branch-cond"><code>{html.escape(b.condition)}</code></div>
  {outcome_html}
</div>""")
        return "\n".join(parts)

    # ── Legend ────────────────────────────────────────────────────────────────

    def _render_legend(self) -> str:
        items = "".join(
            f'<div class="legend-item">'
            f'<div class="legend-dot" style="background:{color}"></div>'
            f'{label}</div>'
            for label, color in [
                ("Extract",   "#7c3aed"),
                ("Map",       "#0891b2"),
                ("Enrich",    "#059669"),
                ("Override",  "#d97706"),
                ("Condition", "#ea580c"),
                ("Final",     "#dc2626"),
                ("Pass",      "#9ca3af"),
                ("Default",   "#6b7280"),
            ]
        )
        return f'<div class="legend">{items}</div>'

    # ── Graph-only export ─────────────────────────────────────────────────────

    def export_graph_only(
        self,
        G: "nx.MultiDiGraph",
        field_name: str,
    ) -> str:
        """Generate a standalone fullscreen HTML page showing only the vis.js
        network built from *G*.

        Unlike ``export()``, this page has no pipeline table, no branches list —
        just the interactive graph with a compact stats bar and a legend.  It is
        intentionally large (full-viewport) so the graph has maximum space.

        Returns the HTML string (does **not** write to disk — the caller handles
        file I/O).
        """
        if G is None or G.number_of_nodes() == 0:
            # Return a minimal page explaining no graph data is available.
            return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<title>Graph: {html.escape(field_name)}</title></head>
<body style="font-family:monospace;padding:40px;color:#6b7280;">
  No graph data available for <strong>{html.escape(field_name)}</strong>.
</body></html>"""

        vis_data   = _nx_to_visjs(G)
        nodes_json = json.dumps(vis_data["nodes"], ensure_ascii=False)
        edges_json = json.dumps(vis_data["edges"], ensure_ascii=False)
        n_nodes    = G.number_of_nodes()
        n_edges    = G.number_of_edges()

        # Build node-type breakdown for the stats bar
        type_counts: dict[str, int] = {}
        for _, data in G.nodes(data=True):
            t = data.get("transformation_type") or "UNKNOWN"
            type_counts[t] = type_counts.get(t, 0) + 1

        stats_chips = "".join(
            f'<span style="background:{_TYPE_COLORS.get(t,"#6b7280")}22;'
            f'color:{_TYPE_COLORS.get(t,"#6b7280")};'
            f'border:1px solid {_TYPE_COLORS.get(t,"#6b7280")}44;'
            f'border-radius:3px;padding:2px 8px;font-size:10px;font-weight:700;'
            f'letter-spacing:0.06em;">'
            f'{_TYPE_LABELS.get(t,t)}&nbsp;{cnt}</span>'
            for t, cnt in sorted(type_counts.items(), key=lambda x: -x[1])
        )

        options_json = json.dumps({
            "layout": {
                "hierarchical": {
                    "enabled":          True,
                    "direction":        "LR",
                    "sortMethod":       "directed",
                    "levelSeparation":  220,
                    "nodeSpacing":      110,
                    "treeSpacing":      140,
                    "blockShifting":    True,
                    "edgeMinimization": True,
                    "parentCentralization": True,
                }
            },
            "physics": {"enabled": False},
            "interaction": {
                "hover":             True,
                "tooltipDelay":      120,
                "navigationButtons": True,
                "keyboard":          True,
                "zoomSpeed":         0.5,
                "multiselect":       True,
            },
            "edges": {
                "smooth": {
                    "type":           "cubicBezier",
                    "forceDirection": "horizontal",
                    "roundness":      0.4,
                }
            },
            "nodes": {"widthConstraint": {"maximum": 200}},
        })

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Graph — {html.escape(field_name)}</title>
<script src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Barlow+Condensed:wght@600;700&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'IBM Plex Mono', monospace;
    background: #f4f5f7;
    color: #111827;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}

  /* ── Top bar ── */
  .topbar {{
    flex-shrink: 0;
    background: #fff;
    border-bottom: 2px solid #dc2626;
    padding: 10px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .topbar-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 20px;
    letter-spacing: 0.06em;
    color: #111827;
    white-space: nowrap;
  }}
  .topbar-title span {{ color: #dc2626; }}
  .topbar-meta {{
    font-size: 10px;
    color: #9ca3af;
    white-space: nowrap;
  }}
  .chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    flex: 1;
    justify-content: flex-end;
  }}

  /* ── Graph fills remaining height ── */
  #graph-container {{
    flex: 1;
    position: relative;
    overflow: hidden;
  }}
  #lineage-graph {{
    width: 100%;
    height: 100%;
    background: #ffffff;
  }}

  /* ── Controls overlay ── */
  .controls {{
    position: absolute;
    bottom: 16px;
    right: 16px;
    background: rgba(255,255,255,0.92);
    border: 1px solid #e2e4e9;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 10px;
    color: #6b7280;
    backdrop-filter: blur(4px);
    line-height: 1.8;
  }}

  /* ── Legend overlay ── */
  .legend {{
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(255,255,255,0.92);
    border: 1px solid #e2e4e9;
    border-radius: 6px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    backdrop-filter: blur(4px);
  }}
  .legend-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: #9ca3af;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 10px;
    color: #374151;
  }}
  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 2px;
    flex-shrink: 0;
  }}
</style>
</head>
<body>

<!-- Top bar -->
<div class="topbar">
  <div class="topbar-title">LINEAGE GRAPH&nbsp;<span>{html.escape(field_name)}</span></div>
  <div class="topbar-meta">{n_nodes} nodes&nbsp;·&nbsp;{n_edges} edges</div>
  <div class="chips">{stats_chips}</div>
</div>

<!-- Full-height graph -->
<div id="graph-container">
  <div id="lineage-graph"></div>

  <!-- Legend -->
  <div class="legend">
    <div class="legend-title">Node type</div>
    {''.join(
        f'<div class="legend-item">'
        f'<div class="legend-dot" style="background:{color}"></div>'
        f'{label}</div>'
        for label, color in [
            ("Extract",   "#7c3aed"),
            ("Map",       "#0891b2"),
            ("Enrich",    "#059669"),
            ("Override",  "#d97706"),
            ("Condition", "#ea580c"),
            ("Final",     "#dc2626"),
            ("Pass",      "#9ca3af"),
            ("Default",   "#6b7280"),
        ]
    )}
  </div>

  <!-- Controls hint -->
  <div class="controls">
    Scroll — zoom&nbsp;&nbsp;·&nbsp;&nbsp;Drag — pan<br/>
    Click node — select&nbsp;&nbsp;·&nbsp;&nbsp;Ctrl+click — multi
  </div>
</div>

<script>
(function() {{
  var container = document.getElementById('lineage-graph');
  var data = {{
    nodes: new vis.DataSet({nodes_json}),
    edges: new vis.DataSet({edges_json}),
  }};
  var options = {options_json};
  var network = new vis.Network(container, data, options);

  // Fit with a short delay to ensure container has rendered
  setTimeout(function() {{ network.fit({{ animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }} }}); }}, 100);

  // Highlight connected nodes on click
  network.on('click', function(params) {{
    if (params.nodes.length > 0) {{
      var nodeId = params.nodes[0];
      var connected = network.getConnectedNodes(nodeId);
      var allNodes = data.nodes.get();
      var updates = allNodes.map(function(n) {{
        var dim = connected.indexOf(n.id) === -1 && n.id !== nodeId;
        return {{
          id: n.id,
          opacity: dim ? 0.25 : 1.0,
        }};
      }});
      data.nodes.update(updates);
    }} else {{
      // click on empty — restore all
      data.nodes.update(data.nodes.get().map(function(n) {{ return {{ id: n.id, opacity: 1.0 }}; }}));
    }}
  }});
}})();
</script>
</body>
</html>"""
