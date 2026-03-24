"""In-house graph visualizer using NetworkX + PyVis with search/filter/focus UI.

Produces:
  - lineage_graph.html / .json  — full graph
  - fields/index.html           — field index with links to per-field pages
  - fields/{FIELD_NAME}.html    — isolated lineage for a single field
  - fields/{FIELD_NAME}.json    — isolated subgraph in Node-Link JSON
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import networkx as nx
from pyvis.network import Network

from orchestrator.models import EdgeType, LineageEdge, LineageNode, NodeType
from orchestrator.storage.base_provider import BaseGraphProvider

NODE_COLORS: dict[NodeType, str] = {
    NodeType.JAVA_CLASS: "#4A90D9",
    NodeType.JAVA_METHOD: "#7EC8E3",
    NodeType.JAVA_FIELD: "#A8D8EA",
    NodeType.JAVA_CONSTANT: "#E67E22",
    NodeType.DTO: "#F5A623",
    NodeType.XSLT_TEMPLATE: "#9B59B6",
    NodeType.XSLT_FIELD: "#C39BD3",
}

EDGE_COLORS: dict[EdgeType, str] = {
    EdgeType.CALLS: "#3498DB",
    EdgeType.DERIVED_FROM: "#E74C3C",
    EdgeType.TRANSFORMS: "#2ECC71",
    EdgeType.UNMARSHALS_TO: "#F39C12",
    EdgeType.CROSS_REPO: "#E91E63",
}

NODE_SHAPES: dict[NodeType, str] = {
    NodeType.JAVA_CLASS: "box",
    NodeType.JAVA_METHOD: "ellipse",
    NodeType.JAVA_FIELD: "diamond",
    NodeType.JAVA_CONSTANT: "square",
    NodeType.DTO: "hexagon",
    NodeType.XSLT_TEMPLATE: "triangle",
    NodeType.XSLT_FIELD: "star",
}

PYVIS_OPTIONS = """{
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -8000,
      "centralGravity": 0.3,
      "springLength": 150,
      "springConstant": 0.04,
      "damping": 0.09
    },
    "minVelocity": 0.75
  },
  "interaction": {
    "hover": true,
    "tooltipDelay": 200,
    "navigationButtons": true,
    "keyboard": true
  },
  "edges": {
    "arrows": { "to": { "enabled": true, "scaleFactor": 0.8 } },
    "smooth": { "type": "cubicBezier", "forceDirection": "horizontal" },
    "font": { "size": 10, "align": "middle" }
  },
  "nodes": {
    "font": { "size": 14 },
    "borderWidth": 2
  }
}"""


class PyVisGraphProvider(BaseGraphProvider):
    """Renders lineage as interactive HTML files — full graph + per-field isolation."""

    def __init__(self, output_dir: Path = Path("output")) -> None:
        self._graph = nx.DiGraph()
        self._output_dir = output_dir

    def add_node(self, node: LineageNode) -> None:
        color = NODE_COLORS.get(node.node_type, "#97c2fc")
        shape = NODE_SHAPES.get(node.node_type, "dot")
        tooltip = self._build_tooltip(node)

        self._graph.add_node(
            node.id,
            label=node.label,
            type=node.node_type.value,
            title=tooltip,
            color=color,
            shape=shape,
            file_path=node.meta.file_path,
            line_number=node.meta.line_number,
            code_snippet=node.meta.code_snippet,
            md5_hash=node.meta.md5_hash,
            **node.properties,
        )

    def add_edge(self, edge: LineageEdge) -> None:
        color = EDGE_COLORS.get(edge.edge_type, "#848484")
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            type=edge.edge_type.value,
            color=color,
            title=edge.edge_type.value,
            label=edge.edge_type.value,
            **edge.properties,
        )

    def export_node_link_json(self) -> dict:
        return nx.node_link_data(self._graph, edges="links")

    def persist(self) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Full graph JSON + HTML
        json_path = self._output_dir / "lineage_graph.json"
        with open(json_path, "w") as f:
            json.dump(self.export_node_link_json(), f, indent=2, default=str)

        html_path = self._output_dir / "lineage_graph.html"
        self._write_html(self._graph, html_path, title="Synapse Trace — Full Lineage")

        print(f"  Graph JSON: {json_path}")
        print(f"  Graph HTML: {html_path}")

        # 2. Per-field isolated subgraphs
        field_dir = self._output_dir / "fields"
        field_dir.mkdir(parents=True, exist_ok=True)

        field_subgraphs = self._extract_field_subgraphs()
        for field_name, subgraph in sorted(field_subgraphs.items()):
            safe_name = _safe_filename(field_name)

            # Per-field JSON
            field_json_path = field_dir / f"{safe_name}.json"
            with open(field_json_path, "w") as f:
                json.dump(nx.node_link_data(subgraph, edges="links"), f, indent=2, default=str)

            # Per-field HTML
            field_html_path = field_dir / f"{safe_name}.html"
            self._write_html(
                subgraph,
                field_html_path,
                title=f"Field Lineage — {field_name}",
                back_link=True,
            )

        # 3. Field index page
        index_path = field_dir / "index.html"
        self._write_field_index(index_path, field_subgraphs)

        print(f"  Per-field pages: {len(field_subgraphs)} fields -> {field_dir}/")
        print(f"  Field index: {index_path}")

    # ------------------------------------------------------------------
    # Per-field subgraph extraction
    # ------------------------------------------------------------------

    def _extract_field_subgraphs(self) -> dict[str, nx.DiGraph]:
        """Extract an isolated subgraph for each unique field.

        A "field" is identified by:
          - XSLT_FIELD nodes: output_element property or label
          - JAVA_FIELD nodes: label
          - JAVA_CONSTANT nodes: bare_name property or label
        """
        # Step 1: Collect seed nodes grouped by canonical field name
        field_seeds: dict[str, set[str]] = defaultdict(set)

        for node_id, data in self._graph.nodes(data=True):
            ntype = data.get("type", "")
            canonical = None

            if ntype == "XSLT_FIELD":
                # The output element is the canonical field name (e.g. N_EFFECTIVE_DATE)
                canonical = data.get("output_element") or data.get("label", "")
            elif ntype == "JAVA_FIELD":
                canonical = data.get("label", "")
            elif ntype == "JAVA_CONSTANT":
                canonical = data.get("bare_name") or data.get("label", "")
                # Strip quotes from string literal labels
                canonical = canonical.strip('"')

            if canonical:
                field_seeds[canonical].add(node_id)

        # Step 2: For each field, walk the graph to collect its full lineage
        result: dict[str, nx.DiGraph] = {}
        undirected = self._graph.to_undirected()

        for field_name, seeds in field_seeds.items():
            reachable: set[str] = set()
            for seed in seeds:
                # BFS walk from each seed node
                reachable |= self._walk_lineage(undirected, seed)

            if not reachable:
                continue

            subgraph = self._graph.subgraph(reachable).copy()
            if subgraph.number_of_nodes() > 0:
                result[field_name] = subgraph

        return result

    @staticmethod
    def _walk_lineage(graph: nx.Graph, start: str, max_depth: int = 10) -> set[str]:
        """BFS walk from a node, collecting all connected nodes up to max_depth."""
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(start, 0)]

        while queue:
            node, depth = queue.pop(0)
            if node in visited or depth > max_depth:
                continue
            visited.add(node)
            for neighbor in graph.neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

        return visited

    # ------------------------------------------------------------------
    # HTML generation
    # ------------------------------------------------------------------

    def _write_html(
        self,
        graph: nx.DiGraph,
        path: Path,
        title: str = "Synapse Trace",
        back_link: bool = False,
    ) -> None:
        net = Network(
            height="900px",
            width="100%",
            directed=True,
            notebook=False,
            cdn_resources="remote",
            bgcolor="#1a1a2e",
            font_color="#e0e0e0",
        )
        net.from_nx(graph)
        net.set_options(PYVIS_OPTIONS)

        html = net.generate_html()
        html = self._inject_search_ui(html, title=title, back_link=back_link)
        path.write_text(html)

    @staticmethod
    def _build_tooltip(node: LineageNode) -> str:
        lines = [
            f"<b>{node.label}</b>",
            f"Type: {node.node_type.value}",
            f"File: {node.meta.file_path}",
            f"Line: {node.meta.line_number}",
            f"MD5: {node.meta.md5_hash[:12]}...",
            f"<pre>{node.meta.code_snippet[:150]}</pre>",
        ]
        for k, v in node.properties.items():
            lines.append(f"{k}: {v}")
        return "<br>".join(lines)

    @staticmethod
    def _inject_search_ui(
        html: str,
        title: str = "Synapse Trace",
        back_link: bool = False,
    ) -> str:
        """Inject search bar, node-type filters, and focus mode into the HTML."""
        back_html = ""
        if back_link:
            back_html = (
                '<div style="margin-bottom:10px">'
                '<a href="index.html" style="color:#7EC8E3;text-decoration:none;font-size:12px">'
                '&larr; Back to Field Index</a>'
                ' &nbsp;|&nbsp; '
                '<a href="../lineage_graph.html" style="color:#7EC8E3;text-decoration:none;font-size:12px">'
                'Full Graph</a>'
                '</div>'
            )

        custom_ui = f"""
<style>
  #synapse-panel {{
    position: fixed; top: 10px; right: 10px; z-index: 9999;
    background: rgba(26, 26, 46, 0.95); border: 1px solid #4A90D9;
    border-radius: 8px; padding: 16px; width: 280px;
    font-family: 'Segoe UI', sans-serif; color: #e0e0e0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    max-height: 90vh; overflow-y: auto;
  }}
  #synapse-panel h3 {{ margin: 0 0 12px; color: #7EC8E3; font-size: 14px; }}
  #synapse-panel input[type="text"] {{
    width: 100%; padding: 8px; border: 1px solid #444;
    border-radius: 4px; background: #16213e; color: #e0e0e0;
    font-size: 13px; box-sizing: border-box; margin-bottom: 10px;
  }}
  #synapse-panel label {{
    display: inline-block; margin: 2px 8px 2px 0; font-size: 12px; cursor: pointer;
  }}
  #synapse-panel .color-dot {{
    display: inline-block; width: 10px; height: 10px;
    border-radius: 50%; margin-right: 4px; vertical-align: middle;
  }}
  #synapse-panel button {{
    margin-top: 10px; padding: 6px 12px; border: none;
    border-radius: 4px; cursor: pointer; font-size: 12px;
    background: #4A90D9; color: white; margin-right: 6px;
  }}
  #synapse-panel button:hover {{ background: #3a7bc8; }}
  #synapse-panel button.secondary {{ background: #555; }}
  #synapse-panel button.secondary:hover {{ background: #666; }}
  #synapse-panel .section {{ margin-top: 10px; padding-top: 8px; border-top: 1px solid #333; }}
  #synapse-panel .stats {{ font-size: 11px; color: #888; margin-top: 8px; }}
  #focus-badge {{
    display: none; background: #E74C3C; color: white; padding: 2px 8px;
    border-radius: 10px; font-size: 11px; margin-left: 8px;
  }}
</style>

<div id="synapse-panel">
  {back_html}
  <h3>{title} <span id="focus-badge">FOCUS MODE</span></h3>
  <input type="text" id="search-input" placeholder="Search nodes..." />
  <div class="section">
    <b style="font-size:12px">Node Types</b><br>
    <label><input type="checkbox" class="type-filter" value="JAVA_CLASS" checked>
      <span class="color-dot" style="background:#4A90D9"></span>Java Class</label>
    <label><input type="checkbox" class="type-filter" value="JAVA_METHOD" checked>
      <span class="color-dot" style="background:#7EC8E3"></span>Method</label>
    <label><input type="checkbox" class="type-filter" value="JAVA_FIELD" checked>
      <span class="color-dot" style="background:#A8D8EA"></span>Field</label>
    <label><input type="checkbox" class="type-filter" value="JAVA_CONSTANT" checked>
      <span class="color-dot" style="background:#E67E22"></span>Constant</label>
    <label><input type="checkbox" class="type-filter" value="DTO" checked>
      <span class="color-dot" style="background:#F5A623"></span>DTO</label>
    <label><input type="checkbox" class="type-filter" value="XSLT_TEMPLATE" checked>
      <span class="color-dot" style="background:#9B59B6"></span>XSLT Template</label>
    <label><input type="checkbox" class="type-filter" value="XSLT_FIELD" checked>
      <span class="color-dot" style="background:#C39BD3"></span>XSLT Field</label>
  </div>
  <div class="section">
    <b style="font-size:12px">Edge Types</b><br>
    <label><input type="checkbox" class="edge-filter" value="CALLS" checked>
      <span class="color-dot" style="background:#3498DB"></span>Calls</label>
    <label><input type="checkbox" class="edge-filter" value="DERIVED_FROM" checked>
      <span class="color-dot" style="background:#E74C3C"></span>Derived From</label>
    <label><input type="checkbox" class="edge-filter" value="TRANSFORMS" checked>
      <span class="color-dot" style="background:#2ECC71"></span>Transforms</label>
    <label><input type="checkbox" class="edge-filter" value="UNMARSHALS_TO" checked>
      <span class="color-dot" style="background:#F39C12"></span>Unmarshals To</label>
    <label><input type="checkbox" class="edge-filter" value="CROSS_REPO" checked>
      <span class="color-dot" style="background:#E91E63"></span>Cross-Repo</label>
  </div>
  <div>
    <button id="reset-btn" class="secondary">Reset View</button>
    <button id="fit-btn" class="secondary">Fit All</button>
  </div>
  <div class="stats" id="stats-line">Nodes: 0 | Edges: 0</div>
</div>

<script>
(function() {{
  var allNodes = null;
  var allEdges = null;
  var focusMode = false;
  var originalColors = {{}};
  var originalEdgeColors = {{}};

  var waitForNetwork = setInterval(function() {{
    if (typeof network !== 'undefined' && network.body && network.body.data) {{
      clearInterval(waitForNetwork);
      init();
    }}
  }}, 200);

  function init() {{
    allNodes = network.body.data.nodes;
    allEdges = network.body.data.edges;

    allNodes.forEach(function(n) {{ originalColors[n.id] = n.color; }});
    allEdges.forEach(function(e) {{ originalEdgeColors[e.id] = e.color; }});

    updateStats();

    document.getElementById('search-input').addEventListener('keyup', function() {{
      var query = this.value.toLowerCase().trim();
      if (!query) {{ resetHighlight(); return; }}
      var updates = [];
      allNodes.forEach(function(n) {{
        var match = (n.label || '').toLowerCase().includes(query) ||
                    (n.id || '').toLowerCase().includes(query);
        updates.push({{id: n.id, opacity: match ? 1.0 : 0.15,
                       color: match ? originalColors[n.id] : '#444'}});
      }});
      allNodes.update(updates);
    }});

    document.querySelectorAll('.type-filter').forEach(function(cb) {{
      cb.addEventListener('change', applyFilters);
    }});
    document.querySelectorAll('.edge-filter').forEach(function(cb) {{
      cb.addEventListener('change', applyFilters);
    }});

    network.on('doubleClick', function(params) {{
      if (params.nodes.length === 0) {{ exitFocus(); return; }}
      enterFocus(params.nodes[0]);
    }});

    document.getElementById('reset-btn').addEventListener('click', function() {{
      exitFocus();
      resetHighlight();
      document.getElementById('search-input').value = '';
      document.querySelectorAll('.type-filter, .edge-filter').forEach(function(cb) {{
        cb.checked = true;
      }});
      applyFilters();
    }});

    document.getElementById('fit-btn').addEventListener('click', function() {{
      network.fit({{animation: true}});
    }});
  }}

  function applyFilters() {{
    var activeTypes = [];
    document.querySelectorAll('.type-filter:checked').forEach(function(cb) {{
      activeTypes.push(cb.value);
    }});
    var activeEdgeTypes = [];
    document.querySelectorAll('.edge-filter:checked').forEach(function(cb) {{
      activeEdgeTypes.push(cb.value);
    }});
    var nodeUpdates = [];
    allNodes.forEach(function(n) {{
      nodeUpdates.push({{id: n.id, hidden: !activeTypes.includes(n.type)}});
    }});
    allNodes.update(nodeUpdates);
    var edgeUpdates = [];
    allEdges.forEach(function(e) {{
      edgeUpdates.push({{id: e.id, hidden: !activeEdgeTypes.includes(e.type)}});
    }});
    allEdges.update(edgeUpdates);
    updateStats();
  }}

  function enterFocus(nodeId) {{
    focusMode = true;
    document.getElementById('focus-badge').style.display = 'inline';
    var connected = network.getConnectedNodes(nodeId);
    connected.push(nodeId);
    var connSet = new Set(connected);
    var updates = [];
    allNodes.forEach(function(n) {{ updates.push({{id: n.id, hidden: !connSet.has(n.id)}}); }});
    allNodes.update(updates);
    var edgeUpdates = [];
    allEdges.forEach(function(e) {{
      edgeUpdates.push({{id: e.id, hidden: !(connSet.has(e.from) && connSet.has(e.to))}});
    }});
    allEdges.update(edgeUpdates);
    network.focus(nodeId, {{scale: 1.2, animation: true}});
    updateStats();
  }}

  function exitFocus() {{
    focusMode = false;
    document.getElementById('focus-badge').style.display = 'none';
    var updates = [];
    allNodes.forEach(function(n) {{ updates.push({{id: n.id, hidden: false}}); }});
    allNodes.update(updates);
    var edgeUpdates = [];
    allEdges.forEach(function(e) {{ edgeUpdates.push({{id: e.id, hidden: false}}); }});
    allEdges.update(edgeUpdates);
    updateStats();
  }}

  function resetHighlight() {{
    var updates = [];
    allNodes.forEach(function(n) {{
      updates.push({{id: n.id, opacity: 1.0, color: originalColors[n.id]}});
    }});
    allNodes.update(updates);
  }}

  function updateStats() {{
    var vn = 0, ve = 0;
    allNodes.forEach(function(n) {{ if (!n.hidden) vn++; }});
    allEdges.forEach(function(e) {{ if (!e.hidden) ve++; }});
    document.getElementById('stats-line').textContent =
      'Nodes: ' + vn + ' | Edges: ' + ve;
  }}
}})();
</script>
"""
        return html.replace("</body>", custom_ui + "\n</body>")

    # ------------------------------------------------------------------
    # Field index page
    # ------------------------------------------------------------------

    @staticmethod
    def _write_field_index(
        path: Path,
        field_subgraphs: dict[str, nx.DiGraph],
    ) -> None:
        """Generate an HTML index page listing all fields with links to individual pages."""

        rows = []
        for field_name in sorted(field_subgraphs):
            sg = field_subgraphs[field_name]
            safe = _safe_filename(field_name)
            node_count = sg.number_of_nodes()
            edge_count = sg.number_of_edges()

            # Collect node types present
            types_present = set()
            repos_present = set()
            for _, data in sg.nodes(data=True):
                types_present.add(data.get("type", ""))
                repo = data.get("repo", "")
                if repo:
                    repos_present.add(repo)

            type_badges = ""
            for t in sorted(types_present):
                color = {
                    "JAVA_CLASS": "#4A90D9", "JAVA_METHOD": "#7EC8E3",
                    "JAVA_FIELD": "#A8D8EA", "JAVA_CONSTANT": "#E67E22",
                    "DTO": "#F5A623", "XSLT_TEMPLATE": "#9B59B6",
                    "XSLT_FIELD": "#C39BD3",
                }.get(t, "#888")
                type_badges += (
                    f'<span style="background:{color};color:#fff;padding:1px 6px;'
                    f'border-radius:3px;font-size:11px;margin-right:3px">{t}</span>'
                )

            repo_text = ", ".join(sorted(repos_present)) if repos_present else "-"

            # Check for cross-repo edges
            cross_repo_count = sum(
                1 for _, _, d in sg.edges(data=True)
                if d.get("type") == "CROSS_REPO"
            )
            cross_badge = ""
            if cross_repo_count:
                cross_badge = (
                    f'<span style="background:#E91E63;color:#fff;padding:1px 6px;'
                    f'border-radius:3px;font-size:11px;margin-left:4px">'
                    f'{cross_repo_count} cross-repo</span>'
                )

            rows.append(f"""
            <tr>
              <td style="font-weight:bold">
                <a href="{safe}.html" style="color:#7EC8E3;text-decoration:none">
                  {field_name}
                </a>
              </td>
              <td>{node_count}</td>
              <td>{edge_count}</td>
              <td>{type_badges}{cross_badge}</td>
              <td>{repo_text}</td>
              <td>
                <a href="{safe}.html" style="color:#7EC8E3;text-decoration:none">View</a>
                &nbsp;|&nbsp;
                <a href="{safe}.json" style="color:#999;text-decoration:none">JSON</a>
              </td>
            </tr>""")

        rows_html = "\n".join(rows)

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Synapse Trace — Field Index</title>
  <style>
    body {{
      background: #1a1a2e; color: #e0e0e0;
      font-family: 'Segoe UI', sans-serif; margin: 0; padding: 30px;
    }}
    h1 {{ color: #7EC8E3; margin-bottom: 5px; }}
    .subtitle {{ color: #888; margin-bottom: 25px; font-size: 14px; }}
    a {{ color: #7EC8E3; }}
    table {{
      width: 100%; border-collapse: collapse; background: rgba(26, 26, 46, 0.8);
      border-radius: 8px; overflow: hidden;
    }}
    th {{
      background: #16213e; padding: 12px 16px; text-align: left;
      font-size: 13px; color: #aaa; border-bottom: 2px solid #333;
    }}
    td {{
      padding: 10px 16px; border-bottom: 1px solid #2a2a4a; font-size: 13px;
    }}
    tr:hover {{ background: rgba(74, 144, 217, 0.1); }}
    .search-box {{
      padding: 10px 14px; border: 1px solid #444; border-radius: 6px;
      background: #16213e; color: #e0e0e0; font-size: 14px; width: 300px;
      margin-bottom: 20px;
    }}
    .nav {{ margin-bottom: 20px; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="nav">
    <a href="../lineage_graph.html">&larr; Full Graph</a>
  </div>
  <h1>Field Lineage Index</h1>
  <p class="subtitle">{len(field_subgraphs)} fields traced — click any field to view its isolated lineage</p>
  <input type="text" class="search-box" id="field-search" placeholder="Filter fields..." />
  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Nodes</th>
        <th>Edges</th>
        <th>Types</th>
        <th>Repos</th>
        <th>Links</th>
      </tr>
    </thead>
    <tbody id="field-table">
      {rows_html}
    </tbody>
  </table>
  <script>
    document.getElementById('field-search').addEventListener('keyup', function() {{
      var q = this.value.toLowerCase();
      var rows = document.querySelectorAll('#field-table tr');
      rows.forEach(function(row) {{
        var text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>"""
        path.write_text(html)


def _safe_filename(name: str) -> str:
    """Convert a field name to a safe filename."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
