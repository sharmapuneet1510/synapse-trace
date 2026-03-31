"""Variable trace service — filters cached lineage for a specific variable and all its name variations.

The service uses _build_match_keys() from the stitcher to automatically generate
all canonical forms of a variable name (camelCase, UPPER_SNAKE_CASE, prefix-stripped, etc.)
and then finds all connected nodes in the lineage graph via BFS.
"""
from __future__ import annotations

import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def _build_match_keys(field_name: str) -> set:  # noqa: E402
    if not field_name:
        return set()
    name = field_name.upper().strip()
    keys = {name}
    for prefix in ("N_", "B_", "S_", "I_", "D_"):
        if name.startswith(prefix):
            keys.add(name[len(prefix):])
    keys.add(name.replace("_", ""))
    return {k for k in keys if k}


from dataclasses import dataclass as _dc, field as _dcf  # noqa: E402
from typing import Any as _Any, List as _List  # noqa: E402

@_dc
class LineageNode:
    id: str = ""
    label: str = ""
    node_type: str = ""
    meta: _Any = None

@_dc
class StitchedLineage:
    nodes: _List[LineageNode] = _dcf(default_factory=list)
    edges: _List[_Any] = _dcf(default_factory=list)

from ..schemas.trace import TraceEdge, TraceNode, TraceResponse  # noqa: E402
from .cache import parse_cache  # noqa: E402

logger = logging.getLogger(__name__)


def _match_node_to_keys(node: LineageNode, target_keys: set[str]) -> bool:
    """Return True if any searchable attribute of node overlaps with target_keys."""
    # Collect all text representations of this node
    searchable: set[str] = {node.label.lower().strip('"'), node.id.lower()}

    for seg in node.id.split("::"):
        searchable.add(seg.lower())
        if "." in seg:
            searchable.add(seg.rsplit(".", 1)[-1].lower())

    for prop_key in ("bare_name", "output_element", "xpath", "qualifier", "owner"):
        val = node.properties.get(prop_key, "")
        if val:
            searchable.add(str(val).lower().strip('"'))

    # Build canonical keys for each searchable string and check overlap
    node_keys: set[str] = set()
    for s in searchable:
        node_keys |= _build_match_keys(s)

    return bool(node_keys & target_keys)


def _bfs_subgraph(
    lineage: StitchedLineage,
    seed_ids: set[str],
    max_depth: int = 15,
) -> tuple[list[LineageNode], list]:
    """BFS from seed nodes to collect all connected nodes/edges."""
    node_by_id = {n.id: n for n in lineage.nodes}

    # Build undirected adjacency
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

    filtered_nodes = [n for n in lineage.nodes if n.id in reachable]
    filtered_edges = [
        e for e in lineage.edges
        if e.source_id in reachable and e.target_id in reachable
    ]
    return filtered_nodes, filtered_edges


def trace_variable(
    variable_name: str,
    jurisdiction_id: str,
    additional_variations: list[str] | None = None,
    max_depth: int = 15,
) -> TraceResponse:
    """
    Trace a variable and all its name variations through the cached lineage graph.

    Strategy:
      1. Generate all canonical forms via _build_match_keys()
      2. Merge with any additional user-provided variations
      3. Find all lineage nodes whose attributes overlap with any of these keys
      4. BFS from seed nodes to collect the full connected subgraph
      5. Return nodes + edges as serialisable dicts

    Args:
        variable_name:        The primary variable name to trace (any form).
        jurisdiction_id:      Which jurisdiction's cache to query.
        additional_variations: Extra name forms to include (e.g. legacy aliases).
        max_depth:            Max BFS hops from seed nodes.

    Returns:
        TraceResponse with nodes, edges, and the full set of variations searched.
    """
    cache = parse_cache.get(jurisdiction_id)
    parse_status = "not_parsed"

    if cache:
        parse_status = cache.status

    if not cache or cache.status != "ready" or not cache.lineage:
        # Return empty graph but still report what variations would be searched
        auto_keys = _build_match_keys(variable_name)
        all_variations = sorted(auto_keys | set(additional_variations or []))
        return TraceResponse(
            variable_name=variable_name,
            jurisdiction_id=jurisdiction_id,
            variations_searched=all_variations,
            nodes=[],
            edges=[],
            node_count=0,
            edge_count=0,
            parse_status=parse_status,
        )

    lineage = cache.lineage

    # ── Step 1: Build target keys ────────────────────────────────────────────
    # Auto-generate all canonical forms (camelCase, UPPER_SNAKE_CASE, etc.)
    target_keys: set[str] = _build_match_keys(variable_name)

    # Add keys from additional user-provided variations
    for extra in (additional_variations or []):
        target_keys |= _build_match_keys(extra)

    # Also add the raw forms themselves
    target_keys.add(variable_name.lower())
    for v in (additional_variations or []):
        target_keys.add(v.lower())

    all_variations = sorted(target_keys)

    logger.info(
        "trace_variable: '%s' in '%s' — %d variation keys: %s",
        variable_name, jurisdiction_id, len(target_keys),
        list(target_keys)[:8],
    )

    # ── Step 2: Find seed nodes ──────────────────────────────────────────────
    seed_ids: set[str] = set()
    for node in lineage.nodes:
        if _match_node_to_keys(node, target_keys):
            seed_ids.add(node.id)
            logger.debug("  Seed: %s (label=%s)", node.id, node.label)

    logger.info("  Found %d seed node(s) for '%s'", len(seed_ids), variable_name)

    if not seed_ids:
        return TraceResponse(
            variable_name=variable_name,
            jurisdiction_id=jurisdiction_id,
            variations_searched=all_variations,
            nodes=[],
            edges=[],
            node_count=0,
            edge_count=0,
            parse_status=parse_status,
        )

    # ── Step 3: BFS subgraph ─────────────────────────────────────────────────
    filtered_nodes, filtered_edges = _bfs_subgraph(lineage, seed_ids, max_depth)

    logger.info(
        "  Trace result: %d nodes, %d edges (from %d seeds)",
        len(filtered_nodes), len(filtered_edges), len(seed_ids),
    )

    # ── Step 4: Serialise ────────────────────────────────────────────────────
    out_nodes = [
        TraceNode(
            id=n.id,
            label=n.label,
            node_type=n.node_type.value if hasattr(n.node_type, "value") else str(n.node_type),
            file_path=str(n.meta.file_path) if n.meta and n.meta.file_path else None,
            line_number=n.meta.line_number if n.meta else None,
            code_snippet=n.meta.code_snippet if n.meta else None,
            properties=dict(n.properties),
        )
        for n in filtered_nodes
    ]

    out_edges = [
        TraceEdge(
            source=e.source_id,
            target=e.target_id,
            type=e.edge_type.value if hasattr(e.edge_type, "value") else str(e.edge_type),
            properties=dict(e.properties),
        )
        for e in filtered_edges
    ]

    return TraceResponse(
        variable_name=variable_name,
        jurisdiction_id=jurisdiction_id,
        variations_searched=all_variations,
        nodes=out_nodes,
        edges=out_edges,
        node_count=len(out_nodes),
        edge_count=len(out_edges),
        parse_status=parse_status,
    )
