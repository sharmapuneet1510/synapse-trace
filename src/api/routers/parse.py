from __future__ import annotations

from fastapi import APIRouter

from ..services import jurisdiction_service
from ..services.cache import parse_cache
from ..services.parse_service import trigger_batch_parse

router = APIRouter(prefix="/api/parse", tags=["parse"])


@router.post("/trigger")
def trigger_parse():
    jurisdictions = jurisdiction_service.get_all()
    started = trigger_batch_parse(jurisdictions)
    if not started:
        return {"status": "already_running", "message": "Batch parse is already in progress"}
    return {"status": "started", "message": f"Parsing {len(jurisdictions)} jurisdictions"}


@router.get("/status")
def parse_status():
    statuses = {}
    for jid in parse_cache.all_ids():
        cache = parse_cache.get(jid)
        if cache:
            statuses[jid] = {
                "status": cache.status,
                "parsed_at": cache.parsed_at.isoformat() if cache.parsed_at else None,
                "java_findings": len(cache.java_findings),
                "xslt_findings": len(cache.xslt_findings),
                "nodes": len(cache.lineage.nodes) if cache.lineage else 0,
                "edges": len(cache.lineage.edges) if cache.lineage else 0,
                "error": cache.error,
            }

    return {
        "batch_status": parse_cache.batch_status,
        "batch_started": parse_cache.batch_started.isoformat() if parse_cache.batch_started else None,
        "batch_completed": parse_cache.batch_completed.isoformat() if parse_cache.batch_completed else None,
        "jurisdictions": statuses,
    }


@router.get("/logs")
def parse_logs(limit: int = 100):
    return parse_cache.get_logs(limit)
