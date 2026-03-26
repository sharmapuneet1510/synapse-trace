from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..schemas.field import FieldDetail
from ..services import field_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fields", tags=["fields"])


@router.get("/{jurisdiction_id}/{field_name}", response_model=FieldDetail)
def get_field_detail(jurisdiction_id: str, field_name: str):
    detail = field_service.get_field_detail(jurisdiction_id, field_name)
    if not detail:
        logger.warning("GET /fields/%s/%s → 404 not found", jurisdiction_id, field_name)
        raise HTTPException(404, f"Field '{field_name}' not found in '{jurisdiction_id}'")
    logger.debug(
        "GET /fields/%s/%s → OK (xpaths=%d, deps=%d, java_refs=%d)",
        jurisdiction_id, field_name,
        len(detail.input_xpaths), len(detail.dependencies), len(detail.java_references),
    )
    return detail
