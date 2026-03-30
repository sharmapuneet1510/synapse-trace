"""GET /graph/field/{field_name} endpoints."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from modules.backend_api.services.trace_service import ApiTraceService
from modules.trace_core.logging.logger_factory import LoggerFactory

router = APIRouter()
logger = LoggerFactory.get("api")
_service = ApiTraceService()


@router.get("/field/{field_name}", summary="Get full lineage graph for a field")
def get_graph(field_name: str):
    try:
        result = _service.trace(field_name=field_name)
        return result.to_json()["graph_json"]
    except Exception as exc:
        logger.exception(f"Graph retrieval failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/field/{field_name}/pipeline", summary="Get pipeline view for a field")
def get_pipeline(field_name: str):
    try:
        result = _service.trace(field_name=field_name)
        return result.to_pipeline_json()
    except Exception as exc:
        logger.exception(f"Pipeline retrieval failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/field/{field_name}/branches", summary="Get branch view for a field")
def get_branches(field_name: str):
    try:
        result = _service.trace(field_name=field_name)
        return result.to_branch_json()
    except Exception as exc:
        logger.exception(f"Branch retrieval failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
