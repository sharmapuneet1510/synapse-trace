"""Pydantic response schema for trace endpoints."""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class EvidenceSchema(BaseModel):
    repository: Optional[str] = None
    module: Optional[str] = None
    package: Optional[str] = None
    class_or_template: Optional[str] = None
    method_or_template_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    transformation_type: Optional[str] = None
    condition_text: Optional[str] = None
    raw_code: Optional[str] = None


class SummarySchema(BaseModel):
    field_name: str
    origin: str
    pipeline_steps: List[str]
    branch_count: int
    total_nodes: int
    has_xslt: bool
    has_java: bool
    technical_explanation: str
    business_explanation: str


class TraceResponse(BaseModel):
    trace_id: str
    field_name: str
    origin: str
    summary: SummarySchema
    pipeline: List[Dict[str, Any]]
    branches: List[Dict[str, Any]]
    evidence: List[EvidenceSchema]
    technical_explanation: str
    business_explanation: str
    graph_json: Dict[str, Any]
    metadata: Dict[str, Any] = {}
