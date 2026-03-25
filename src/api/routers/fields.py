from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.field import FieldDetail
from ..services import field_service

router = APIRouter(prefix="/api/fields", tags=["fields"])


@router.get("/{jurisdiction_id}/{field_name}", response_model=FieldDetail)
def get_field_detail(jurisdiction_id: str, field_name: str):
    detail = field_service.get_field_detail(jurisdiction_id, field_name)
    if not detail:
        raise HTTPException(404, f"Field '{field_name}' not found in '{jurisdiction_id}'")
    return detail
