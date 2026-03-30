"""POST /trace/field endpoint."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from modules.backend_api.schemas.trace_request import TraceRequest
from modules.backend_api.schemas.trace_response import TraceResponse, SummarySchema, EvidenceSchema
from modules.backend_api.services.trace_service import ApiTraceService
from modules.trace_core.logging.logger_factory import LoggerFactory

router = APIRouter()
logger = LoggerFactory.get("api")
_service = ApiTraceService()


@router.post("/field", response_model=TraceResponse, summary="Trace a field's lineage")
def trace_field(req: TraceRequest):
    """Run a full field lineage trace and return structured results."""
    logger.info(f"POST /trace/field field={req.field_name}", field_name=req.field_name)
    try:
        result = _service.trace(
            field_name=req.field_name,
            jurisdiction=req.jurisdiction,
            package_filters=req.package_filters,
            max_depth=req.max_depth,
            enable_condition_tracing=req.enable_condition_tracing,
            enable_xslt_imports=req.enable_xslt_imports,
        )
        payload = result.to_json()
        pipeline_data = result.to_pipeline_json()

        return TraceResponse(
            trace_id=result.trace_id,
            field_name=result.field_name,
            origin=result.summary.origin.value,
            summary=SummarySchema(**result.summary.to_dict()),
            pipeline=pipeline_data.get("steps", []),
            branches=[b.to_dict() for b in result.branches],
            evidence=[EvidenceSchema(**e.to_dict()) for e in result.evidence_list],
            technical_explanation=result.summary.technical_explanation,
            business_explanation=result.summary.business_explanation,
            graph_json=payload.get("graph_json", {}),
            metadata=result.metadata,
        )
    except Exception as exc:
        logger.exception(f"Trace failed for field {req.field_name}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
