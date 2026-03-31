"""Variable trace router — POST /api/trace/variable."""
from __future__ import annotations

import logging

from fastapi import APIRouter

from ..schemas.trace import TraceRequest, TraceResponse
from ..services.trace_service import trace_variable

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trace", tags=["trace"])


@router.post("/variable", response_model=TraceResponse)
def trace_variable_endpoint(req: TraceRequest) -> TraceResponse:
    """
    Trace a variable name (and all its canonical variations) through the
    parsed lineage graph for a given jurisdiction.

    All name forms are auto-generated:
      - N_EFFECTIVE_DATE → effectiveDate, EFFECTIVE_DATE, nEffectiveDate, ...
      - effectiveDate    → N_EFFECTIVE_DATE, EFFECTIVE_DATE, ...

    Additional custom variations can be passed via `additional_variations`.

    Returns a subgraph of all nodes and edges connected to any variation of
    the requested variable.

    Requires: a batch parse must have been run for the jurisdiction first.
    """
    logger.info(
        "POST /trace/variable: '%s' in '%s' (extras=%d, max_depth=%d)",
        req.variable_name, req.jurisdiction_id,
        len(req.additional_variations), req.max_depth,
    )
    result = trace_variable(
        variable_name=req.variable_name,
        jurisdiction_id=req.jurisdiction_id,
        additional_variations=req.additional_variations,
        max_depth=req.max_depth,
    )
    logger.info(
        "POST /trace/variable: '%s' → %d nodes, %d edges, status=%s",
        req.variable_name, result.node_count, result.edge_count, result.parse_status,
    )
    return result
