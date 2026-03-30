"""Pydantic request schema for POST /trace/field."""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field


class TraceRequest(BaseModel):
    field_name: str = Field(..., description="Name of the field to trace", min_length=1)
    jurisdiction: Optional[str] = Field(None, description="Optional jurisdiction filter")
    package_filters: Optional[List[str]] = Field(None, description="Optional package include patterns")
    max_depth: int = Field(20, ge=1, le=50, description="Maximum call-chain recursion depth")
    enable_condition_tracing: bool = Field(True, description="Enable branch condition analysis")
    enable_xslt_imports: bool = Field(True, description="Follow xsl:import and xsl:include")

    model_config = {"json_schema_extra": {"example": {"field_name": "N_CLEARED", "jurisdiction": "US", "max_depth": 20}}}
