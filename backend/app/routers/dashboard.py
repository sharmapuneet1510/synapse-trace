"""Dashboard API — batch status, live logs, node/edge stats."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..services.cache import parse_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats():
    """Get aggregate stats across all jurisdictions."""
    total_java = 0
    total_xslt = 0
    total_nodes = 0
    total_edges = 0
    jurisdictions = []

    for jid in parse_cache.all_ids():
        cache = parse_cache.get(jid)
        if not cache:
            continue
        j_java = len(cache.java_findings)
        j_xslt = len(cache.xslt_findings)
        j_nodes = len(cache.lineage.nodes) if cache.lineage else 0
        j_edges = len(cache.lineage.edges) if cache.lineage else 0

        total_java += j_java
        total_xslt += j_xslt
        total_nodes += j_nodes
        total_edges += j_edges

        jurisdictions.append({
            "id": jid,
            "status": cache.status,
            "java_findings": j_java,
            "xslt_findings": j_xslt,
            "nodes": j_nodes,
            "edges": j_edges,
            "parsed_at": cache.parsed_at.isoformat() if cache.parsed_at else None,
        })

    return {
        "batch_status": parse_cache.batch_status,
        "batch_started": parse_cache.batch_started.isoformat() if parse_cache.batch_started else None,
        "batch_completed": parse_cache.batch_completed.isoformat() if parse_cache.batch_completed else None,
        "totals": {
            "java_findings": total_java,
            "xslt_findings": total_xslt,
            "nodes": total_nodes,
            "edges": total_edges,
        },
        "jurisdictions": jurisdictions,
    }


@router.get("/nodes/{jurisdiction_id}")
def get_nodes(jurisdiction_id: str, limit: int = 100, offset: int = 0):
    """Get nodes for a jurisdiction (paginated)."""
    cache = parse_cache.get(jurisdiction_id)
    if not cache or not cache.lineage:
        return {"nodes": [], "total": 0}

    nodes = cache.lineage.nodes[offset : offset + limit]
    return {
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "type": n.node_type.value if hasattr(n.node_type, "value") else str(n.node_type),
                "file_path": n.meta.file_path if n.meta else None,
                "line_number": n.meta.line_number if n.meta else None,
                "code_snippet": n.meta.code_snippet if n.meta else None,
            }
            for n in nodes
        ],
        "total": len(cache.lineage.nodes),
    }


@router.get("/edges/{jurisdiction_id}")
def get_edges(jurisdiction_id: str, limit: int = 100, offset: int = 0):
    """Get edges for a jurisdiction (paginated)."""
    cache = parse_cache.get(jurisdiction_id)
    if not cache or not cache.lineage:
        return {"edges": [], "total": 0}

    edges = cache.lineage.edges[offset : offset + limit]
    return {
        "edges": [
            {
                "source": e.source_id,
                "target": e.target_id,
                "type": e.edge_type.value if hasattr(e.edge_type, "value") else str(e.edge_type),
            }
            for e in edges
        ],
        "total": len(cache.lineage.edges),
    }


@router.get("/live")
async def live_logs(request: Request):
    """SSE endpoint for live batch parse logs."""
    logger.info("SSE client connected: GET /dashboard/live")

    async def event_stream():
        last_index = 0
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected from /dashboard/live")
                    break

                logs = parse_cache.get_logs(500)
                if len(logs) > last_index:
                    new_logs = logs[last_index:]
                    for log in new_logs:
                        yield f"data: {json.dumps(log)}\n\n"
                    last_index = len(logs)

                status = {
                    "type": "heartbeat",
                    "batch_status": parse_cache.batch_status,
                    "timestamp": datetime.now().isoformat(),
                }
                yield f"data: {json.dumps(status)}\n\n"

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("SSE stream cancelled for /dashboard/live")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
