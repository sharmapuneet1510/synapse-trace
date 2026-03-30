#!/usr/bin/env python3
"""Demonstrates all TraceResult export methods as per the requirements."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.trace_core.tracing.trace_service import TraceService

os.makedirs("outputs/html", exist_ok=True)
os.makedirs("outputs/json", exist_ok=True)

service = TraceService()

# ── Example 1: Basic trace ──────────────────────────────────────────
print("=" * 60)
print("Example 1 – Basic Trace")
print("=" * 60)
trace = service.trace(field_name="N_CLEARED")
print(f"Trace ID : {trace.trace_id}")
print(f"Summary  : {trace.summary.to_dict()}")

# ── Example 2: Convert to NetworkX graph ────────────────────────────
print("\n" + "=" * 60)
print("Example 2 – NetworkX Graph")
print("=" * 60)
graph = trace.to_graph()
print(f"Nodes ({graph.number_of_nodes()}):")
for nid, attrs in list(graph.nodes(data=True))[:3]:
    print(f"  {nid}: {attrs.get('label')}")
print(f"Edges ({graph.number_of_edges()}):")
for u, v, data in list(graph.edges(data=True))[:3]:
    print(f"  {u} --[{data.get('relation')}]--> {v}")

# ── Example 3: Export to HTML ───────────────────────────────────────
print("\n" + "=" * 60)
print("Example 3 – HTML Export")
print("=" * 60)
html = trace.to_html()
out_path = "outputs/html/n_cleared_trace.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Saved: {out_path} ({len(html)} bytes)")

# ── Example 4: JSON export ──────────────────────────────────────────
print("\n" + "=" * 60)
print("Example 4 – JSON Export")
print("=" * 60)
payload = trace.to_json()
out_path = "outputs/json/n_cleared_trace.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, default=str)
print(f"Saved: {out_path}")
print(f"Keys: {list(payload.keys())}")

# ── Example 5: Pipeline JSON ────────────────────────────────────────
print("\n" + "=" * 60)
print("Example 5 – Pipeline JSON")
print("=" * 60)
pipeline = trace.to_pipeline_json()
print(f"Total steps: {pipeline.get('total_steps', 0)}")
for step in pipeline.get("steps", [])[:3]:
    print(f"  Step {step['order']}: {step['label']} [{step.get('transformation_type')}]")

# ── Example 6: Branch JSON ──────────────────────────────────────────
print("\n" + "=" * 60)
print("Example 6 – Branch JSON")
print("=" * 60)
branches = trace.to_branch_json()
print(f"Branch count: {branches.get('branch_count', 0)}")
for b in branches.get("branches", [])[:3]:
    print(f"  [{b['branch_id']}] {b['condition']} → {b.get('outcome')}")

# ── Example 7: Neo4j export ─────────────────────────────────────────
print("\n" + "=" * 60)
print("Example 7 – Neo4j Export")
print("=" * 60)
neo4j = trace.to_neo4j()
print(f"Neo4j nodes       : {len(neo4j.get('nodes', []))}")
print(f"Neo4j relationships: {len(neo4j.get('relationships', []))}")
print(f"Cypher statements  : {len(neo4j.get('cypher_statements', []))}")
print("\nFirst 2 Cypher statements:")
for stmt in neo4j.get("cypher_statements", [])[:2]:
    print(f"  {stmt[:100]}")

print("\n[Done] All examples complete.")
