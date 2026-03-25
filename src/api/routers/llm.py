"""LLM utility endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.llm_service import llm_service

router = APIRouter(prefix="/api/llm", tags=["llm"])


class DescribeRequest(BaseModel):
    field_name: str
    jurisdiction_id: str
    code_logic: str | None = None
    xpaths: list[str] | None = None


class DescribeResponse(BaseModel):
    field_name: str
    jurisdiction_id: str
    description: str


@router.post("/describe", response_model=DescribeResponse)
async def describe_field(body: DescribeRequest):
    description = await llm_service.generate_business_description(
        field_name=body.field_name,
        jurisdiction_id=body.jurisdiction_id,
        code_logic=body.code_logic,
        xpaths=body.xpaths,
    )
    return DescribeResponse(
        field_name=body.field_name,
        jurisdiction_id=body.jurisdiction_id,
        description=description,
    )
