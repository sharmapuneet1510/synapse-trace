"""Live dashboard — real-time processing monitor with graph built on the fly.

Starts a local web server that:
  - Serves a dashboard HTML page
  - Streams processing events via Server-Sent Events (SSE)
  - Shows live stats: files scanned, findings, nodes, edges
  - Renders the lineage graph incrementally as nodes/edges are created

Usage:
    # In one terminal — start dashboard:
    python -m orchestrator.dashboard --port 8765

    # In another terminal (or same script) — run trace with live events:
    from orchestrator import live_events
    from orchestrator.quick_trace import trace_project

    live_events.enable()
    result = trace_project(main="/code/my-app", libs=["/code/lib-fields"])

    # Open http://localhost:8765 in a browser to watch live
"""

from __future__ import annotations

import json
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Union

from orchestrator import live_events
from orchestrator.quick_trace import trace_project, trace

logger = logging.getLogger(__name__)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Synapse Trace — Live Dashboard</title>
  <script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0d1117; color: #c9d1d9;
      font-family: 'Segoe UI', -apple-system, sans-serif;
    }
    .header {
      background: #161b22; border-bottom: 1px solid #30363d;
      padding: 12px 24px; display: flex; align-items: center; gap: 16px;
    }
    .header h1 { font-size: 18px; color: #58a6ff; font-weight: 600; }
    .header .status {
      font-size: 12px; padding: 3px 10px; border-radius: 12px;
      background: #1f6feb22; color: #58a6ff; border: 1px solid #1f6feb;
    }
    .header .status.active { background: #23882322; color: #3fb950; border-color: #238823; }
    .header .status.done { background: #8b949e22; color: #8b949e; border-color: #30363d; }

    .container { display: flex; height: calc(100vh - 52px); }

    /* Left panel — stats & log */
    .panel {
      width: 360px; min-width: 320px;
      background: #161b22; border-right: 1px solid #30363d;
      display: flex; flex-direction: column; overflow: hidden;
    }

    .stats-grid {
      display: grid; grid-template-columns: 1fr 1fr;
      gap: 8px; padding: 16px;
    }
    .stat-card {
      background: #0d1117; border: 1px solid #30363d; border-radius: 8px;
      padding: 12px; text-align: center;
    }
    .stat-card .value {
      font-size: 28px; font-weight: 700; color: #58a6ff;
      font-variant-numeric: tabular-nums;
    }
    .stat-card .label { font-size: 11px; color: #8b949e; margin-top: 2px; text-transform: uppercase; }
    .stat-card.nodes .value { color: #3fb950; }
    .stat-card.edges .value { color: #f0883e; }
    .stat-card.matches .value { color: #d2a8ff; }
    .stat-card.files .value { color: #79c0ff; }

    .phase-bar {
      padding: 8px 16px; font-size: 12px; color: #8b949e;
      background: #0d1117; border-top: 1px solid #21262d;
      border-bottom: 1px solid #21262d;
    }
    .phase-bar .phase-name { color: #d2a8ff; font-weight: 600; }

    .log-container {
      flex: 1; overflow-y: auto; padding: 8px 12px;
      font-family: 'SFMono-Regular', 'Cascadia Code', monospace; font-size: 11px;
    }
    .log-entry {
      padding: 3px 0; border-bottom: 1px solid #21262d11;
      display: flex; gap: 6px; line-height: 1.4;
    }
    .log-entry .ts { color: #484f58; min-width: 70px; }
    .log-entry .tag {
      padding: 0 5px; border-radius: 3px; font-size: 10px;
      font-weight: 600; min-width: 50px; text-align: center;
    }
    .tag.scan { background: #1f6feb33; color: #58a6ff; }
    .tag.parse { background: #23882333; color: #3fb950; }
    .tag.node { background: #3fb95033; color: #56d364; }
    .tag.edge { background: #f0883e33; color: #f0883e; }
    .tag.match { background: #d2a8ff33; color: #d2a8ff; }
    .tag.stitch { background: #da3633; color: #ff7b72; }
    .tag.trace { background: #79c0ff33; color: #79c0ff; }
    .tag.lib { background: #f778ba33; color: #f778ba; }
    .log-entry .msg { color: #c9d1d9; }

    /* Right panel — live graph */
    .graph-container { flex: 1; position: relative; }
    #graph { width: 100%; height: 100%; }

    .graph-legend {
      position: absolute; bottom: 12px; left: 12px;
      background: #161b22ee; border: 1px solid #30363d;
      border-radius: 8px; padding: 10px 14px; font-size: 11px;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; margin: 3px 0; }
    .legend-dot {
      width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0;
    }

    .graph-controls {
      position: absolute; top: 12px; right: 12px;
      display: flex; gap: 6px;
    }
    .graph-controls button {
      background: #21262d; border: 1px solid #30363d; color: #c9d1d9;
      padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
    }
    .graph-controls button:hover { background: #30363d; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Synapse Trace</h1>
    <span class="status" id="status">Waiting</span>
  </div>
  <div class="container">
    <div class="panel">
      <div class="stats-grid">
        <div class="stat-card files"><div class="value" id="s-files">0</div><div class="label">Files Scanned</div></div>
        <div class="stat-card"><div class="value" id="s-findings">0</div><div class="label">Findings</div></div>
        <div class="stat-card nodes"><div class="value" id="s-nodes">0</div><div class="label">Nodes</div></div>
        <div class="stat-card edges"><div class="value" id="s-edges">0</div><div class="label">Edges</div></div>
        <div class="stat-card matches"><div class="value" id="s-matches">0</div><div class="label">Matches</div></div>
        <div class="stat-card"><div class="value" id="s-libs">0</div><div class="label">Libs Resolved</div></div>
      </div>
      <div class="phase-bar">Phase: <span class="phase-name" id="phase">Idle</span></div>
      <div class="log-container" id="log"></div>
    </div>
    <div class="graph-container">
      <div id="graph"></div>
      <div class="graph-controls">
        <button onclick="network.fit({animation:true})">Fit</button>
        <button onclick="togglePhysics()">Physics</button>
        <button onclick="clearGraph()">Clear</button>
      </div>
      <div class="graph-legend">
        <div class="legend-item"><div class="legend-dot" style="background:#4A90D9"></div>Java Class</div>
        <div class="legend-item"><div class="legend-dot" style="background:#7EC8E3"></div>Method</div>
        <div class="legend-item"><div class="legend-dot" style="background:#A8D8EA"></div>Field</div>
        <div class="legend-item"><div class="legend-dot" style="background:#E67E22"></div>Constant</div>
        <div class="legend-item"><div class="legend-dot" style="background:#F5A623"></div>DTO</div>
        <div class="legend-item"><div class="legend-dot" style="background:#8E44AD"></div>XSLT File</div>
        <div class="legend-item"><div class="legend-dot" style="background:#9B59B6"></div>XSLT Template</div>
        <div class="legend-item"><div class="legend-dot" style="background:#C39BD3"></div>XSLT Field</div>
      </div>
    </div>
  </div>

<script>
var NODE_COLORS = {
  JAVA_CLASS: '#4A90D9', JAVA_METHOD: '#7EC8E3', JAVA_FIELD: '#A8D8EA',
  JAVA_CONSTANT: '#E67E22', DTO: '#F5A623',
  XSLT_FILE: '#8E44AD', XSLT_TEMPLATE: '#9B59B6', XSLT_FIELD: '#C39BD3'
};
var NODE_SHAPES = {
  JAVA_CLASS: 'box', JAVA_METHOD: 'ellipse', JAVA_FIELD: 'diamond',
  JAVA_CONSTANT: 'square', DTO: 'hexagon',
  XSLT_FILE: 'database', XSLT_TEMPLATE: 'triangle', XSLT_FIELD: 'star'
};
var EDGE_COLORS = {
  CALLS: '#3498DB', DERIVED_FROM: '#E74C3C', TRANSFORMS: '#2ECC71',
  UNMARSHALS_TO: '#F39C12', CROSS_REPO: '#E91E63', LOADS_XSLT: '#00BCD4'
};

var nodes = new vis.DataSet([]);
var edges = new vis.DataSet([]);
var container = document.getElementById('graph');
var network = new vis.Network(container, {nodes: nodes, edges: edges}, {
  physics: {
    barnesHut: { gravitationalConstant: -6000, centralGravity: 0.2, springLength: 120, springConstant: 0.04 },
    minVelocity: 0.75
  },
  interaction: { hover: true, tooltipDelay: 200 },
  edges: {
    arrows: { to: { enabled: true, scaleFactor: 0.7 } },
    smooth: { type: 'cubicBezier', forceDirection: 'horizontal' },
    font: { size: 9, color: '#8b949e', align: 'middle' }
  },
  nodes: {
    font: { size: 12, color: '#c9d1d9' },
    borderWidth: 2
  }
});

var physicsOn = true;
function togglePhysics() {
  physicsOn = !physicsOn;
  network.setOptions({physics: {enabled: physicsOn}});
}
function clearGraph() {
  nodes.clear();
  edges.clear();
}

var stats = {files: 0, findings: 0, nodes: 0, edges: 0, matches: 0, libs: 0};
var edgeIdCounter = 0;
var knownNodeIds = new Set();
var knownEdgeKeys = new Set();
var logEl = document.getElementById('log');
var maxLog = 500;
var logCount = 0;

function updateStat(key, val) {
  stats[key] = val;
  document.getElementById('s-' + key).textContent = val;
}

function addLog(tag, msg) {
  logCount++;
  if (logCount > maxLog) {
    var first = logEl.firstChild;
    if (first) logEl.removeChild(first);
  }
  var d = document.createElement('div');
  d.className = 'log-entry';
  var now = new Date();
  var ts = now.toTimeString().substring(0, 8);
  d.innerHTML = '<span class="ts">' + ts + '</span>' +
    '<span class="tag ' + tag + '">' + tag.toUpperCase() + '</span>' +
    '<span class="msg">' + msg + '</span>';
  logEl.appendChild(d);
  logEl.scrollTop = logEl.scrollHeight;
}

function handleEvent(evt) {
  var e = evt.event;
  var d = evt.data;

  switch (e) {
    case 'scan_start':
      document.getElementById('status').className = 'status active';
      document.getElementById('status').textContent = 'Scanning';
      document.getElementById('phase').textContent = 'Scanning ' + (d.name || '');
      addLog('scan', 'Scanning ' + (d.type || '') + ': ' + (d.name || '') + ' at ' + (d.root || ''));
      break;

    case 'scan_file':
      updateStat('files', stats.files + 1);
      addLog('scan', d.type + ': ' + (d.file || '').split('/').pop());
      break;

    case 'scan_ref':
      addLog('scan', 'XSLT ref [' + d.ref_type + '] ' + d.xslt_name + ' in ' + d.java_class + '.' + d.method + '() -> ' + (d.resolved || 'unresolved'));
      break;

    case 'scan_complete':
      addLog('scan', 'Complete: ' + d.modules + ' modules, ' + d.java_files + ' java, ' + d.xslt_files + ' xslt');
      break;

    case 'parse_start':
      document.getElementById('status').textContent = 'Parsing';
      addLog('parse', d.parser + ': ' + (d.file || '').split('/').pop());
      break;

    case 'parse_complete':
      updateStat('findings', stats.findings + (d.findings || 0));
      addLog('parse', d.parser + ' done: ' + d.findings + ' findings from ' + (d.file || '').split('/').pop());
      break;

    case 'stitch_start':
      document.getElementById('status').textContent = 'Stitching';
      document.getElementById('phase').textContent = 'Stitching';
      addLog('stitch', 'Starting: ' + d.java_findings + ' java + ' + d.xslt_findings + ' xslt');
      break;

    case 'stitch_phase':
      document.getElementById('phase').textContent = 'Phase ' + d.phase + ': ' + d.name;
      addLog('stitch', 'Phase ' + d.phase + ': ' + d.name);
      break;

    case 'node_added':
      if (!knownNodeIds.has(d.id)) {
        knownNodeIds.add(d.id);
        var ntype = d.type || 'JAVA_CLASS';
        nodes.add({
          id: d.id,
          label: d.label || d.id.split('::').pop(),
          color: NODE_COLORS[ntype] || '#888',
          shape: NODE_SHAPES[ntype] || 'dot',
          title: ntype + ': ' + d.label + '\\n' + d.id
        });
        updateStat('nodes', stats.nodes + 1);
        addLog('node', '[' + ntype + '] ' + (d.label || d.id));
      }
      break;

    case 'edge_added':
      var edgeKey = d.source + '|' + d.target + '|' + d.type;
      if (!knownEdgeKeys.has(edgeKey) && knownNodeIds.has(d.source) && knownNodeIds.has(d.target)) {
        knownEdgeKeys.add(edgeKey);
        edgeIdCounter++;
        edges.add({
          id: 'e' + edgeIdCounter,
          from: d.source,
          to: d.target,
          color: EDGE_COLORS[d.type] || '#848484',
          label: d.type,
          title: d.type
        });
        updateStat('edges', stats.edges + 1);
        addLog('edge', '[' + d.type + '] ' + d.source.split('::').pop() + ' -> ' + d.target.split('::').pop());
      }
      break;

    case 'match_found':
      updateStat('matches', stats.matches + 1);
      addLog('match', 'Key "' + d.match_key + '": ' + d.xslt_count + ' XSLT x ' + d.java_count + ' Java');
      break;

    case 'stitch_complete':
      addLog('stitch', 'Complete: ' + d.nodes + ' nodes, ' + d.edges + ' edges');
      break;

    case 'trace_start':
      document.getElementById('status').className = 'status active';
      document.getElementById('status').textContent = 'Tracing';
      addLog('trace', d.function + ': main=' + (d.main || '') + ' libs=' + (d.libs || []).join(', '));
      break;

    case 'lib_search':
      addLog('lib', 'Searching ' + d.lib_name + ' for: ' + (d.target_classes || []).join(', '));
      break;

    case 'lib_found':
      updateStat('libs', stats.libs + 1);
      addLog('lib', 'Found ' + d.class_name + ' in ' + (d.file || '').split('/').pop());
      break;

    case 'trace_complete':
      document.getElementById('status').className = 'status done';
      document.getElementById('status').textContent = 'Done';
      document.getElementById('phase').textContent = 'Complete';
      addLog('trace', 'Done: ' + d.nodes + ' nodes, ' + d.edges + ' edges');
      network.fit({animation: true});
      break;
  }
}

// SSE connection
var evtSource = new EventSource('/events');
evtSource.onmessage = function(e) {
  try {
    var evt = JSON.parse(e.data);
    handleEvent(evt);
  } catch(err) {
    console.error('Parse error:', err, e.data);
  }
};
evtSource.onerror = function() {
  document.getElementById('status').className = 'status';
  document.getElementById('status').textContent = 'Disconnected';
};
</script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the dashboard — serves HTML and SSE event stream."""

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            self._serve_html()
        elif self.path == "/events":
            self._serve_sse()
        elif self.path == "/stats":
            self._serve_json(live_events.stats())
        elif self.path == "/history":
            self._serve_json(live_events.get_bus().get_history())
        else:
            self.send_error(404)

    def _serve_html(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(DASHBOARD_HTML.encode())

    def _serve_json(self, data: dict | list) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _serve_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            for event in live_events.subscribe(include_history=True):
                line = f"data: {event.to_json()}\n\n"
                self.wfile.write(line.encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args) -> None:
        """Suppress default HTTP access logs."""
        pass


def start_dashboard(port: int = 8765, open_browser: bool = True) -> HTTPServer:
    """Start the dashboard server in a background thread.

    Returns the server instance (call server.shutdown() to stop).
    """
    live_events.enable()

    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://localhost:{port}"
    logger.info("Dashboard running at %s", url)
    print(f"Dashboard running at {url}")

    if open_browser:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass

    return server


def main() -> None:
    """CLI: start dashboard and optionally run a trace."""
    import argparse

    parser = argparse.ArgumentParser(description="Synapse Trace Live Dashboard")
    parser.add_argument("--port", type=int, default=8765, help="Dashboard port (default: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")

    # Optional: run a trace from CLI
    parser.add_argument("--main", help="Main project path to trace")
    parser.add_argument("--libs", nargs="*", default=[], help="Library project paths")
    parser.add_argument("--targets", nargs="*", default=None, help="Specific targets to trace")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s | %(levelname)s | %(message)s",
    )

    server = start_dashboard(port=args.port, open_browser=not args.no_browser)

    if args.main:
        # Give browser a moment to connect
        time.sleep(1.5)
        print(f"\nTracing: main={args.main}, libs={args.libs}")
        result = trace_project(
            main=args.main,
            libs=args.libs,
            targets=args.targets,
        )
        result.print_summary()
        print("\nDashboard still running. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
        server.shutdown()


if __name__ == "__main__":
    main()
