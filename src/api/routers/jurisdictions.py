from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.jurisdiction import ConfigTypeResponse, JurisdictionSummary
from ..services import jurisdiction_service

router = APIRouter(prefix="/api/jurisdictions", tags=["jurisdictions"])


@router.get("", response_model=list[JurisdictionSummary])
def list_jurisdictions():
    result = []
    for j in jurisdiction_service.get_all():
        field_count = sum(len(c.fields) for c in j.configs.values())
        result.append(
            JurisdictionSummary(
                id=j.id,
                name=j.name,
                display_name=j.display_name,
                module_type=j.module_type,
                config_types=list(j.configs.keys()),
                field_count=field_count,
            )
        )
    return result


@router.get("/{jurisdiction_id}")
def get_jurisdiction(jurisdiction_id: str):
    j = jurisdiction_service.get_by_id(jurisdiction_id)
    if not j:
        raise HTTPException(404, f"Jurisdiction '{jurisdiction_id}' not found")
    return j


@router.get("/{jurisdiction_id}/configs/{config_type}", response_model=ConfigTypeResponse)
def get_config_type(jurisdiction_id: str, config_type: str):
    ct = jurisdiction_service.get_config_type(jurisdiction_id, config_type)
    if ct is None:
        raise HTTPException(404, f"Config type '{config_type}' not found")
    return ConfigTypeResponse(
        config_type=config_type,
        jurisdiction_id=jurisdiction_id,
        fields=ct.fields,
    )
