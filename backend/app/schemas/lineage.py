"""Pydantic schemas for the /api/lineage endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    """Request body for POST /api/lineage/scan."""
    field_name: str = Field(..., description="Output field to trace, e.g. N_CLEARED")
    project_repos: List[str] = Field(..., description="Paths to main project repositories")
    lib_repos: List[str] = Field(default_factory=list, description="Paths to shared library repos")
    deep_scan_packages: List[str] = Field(
        default_factory=list,
        description="Java packages to trace deeply, e.g. ['com.abc.*']",
    )
    extraction: List[str] = Field(
        default=[".xslt", ".xsl"],
        description="File extensions treated as extraction phase",
    )
    transformation: List[str] = Field(
        default=[".java"],
        description="File extensions treated as transformation phase",
    )
    max_depth: int = Field(default=20, ge=1, le=50)
    enable_condition_tracing: bool = True
    enable_xslt_imports: bool = True


class DeriveRequest(BaseModel):
    """Request body for POST /api/lineage/derive.

    Runs a named or custom Jinja2 prompt against a pre-computed trace result.

    Prompt resolution order:
      1. custom_prompt (Jinja2 string) — when provided, prompt_name is ignored
      2. prompt_name   (registered template name)

    Context variables available in custom_prompt:
      {{ field_name }}, {{ origin }}, {{ total_nodes }}, {{ branch_count }},
      {{ nodes }}, {{ branches }}, {{ pipeline_steps }}, {{ metadata }},
      {{ downstream_name }}, {{ downstream_packages }}, etc.
    """
    field_name: str
    project_repos: List[str]
    lib_repos: List[str] = Field(default_factory=list)
    deep_scan_packages: List[str] = Field(default_factory=list)
    prompt_name: str = Field(
        default="business_derivation",
        description=(
            "Named Jinja2 template: business_derivation | technical_summary | "
            "reporting_logic | enrichment_logic | downstream_impact | "
            "examples | operations | field_impact | chat_context"
        ),
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        description=(
            "Raw Jinja2 template string. When set, prompt_name is ignored. "
            "All graph context variables are available. Example: "
            "'Explain {{ field_name }} which has {{ branch_count }} branches.'"
        ),
    )


# ── Evidence / node schemas ───────────────────────────────────────────────────

class EvidenceSchema(BaseModel):
    file_path: Optional[str] = None
    class_or_template: Optional[str] = None
    method_or_template_name: Optional[str] = None
    line_number: Optional[int] = None
    condition_text: Optional[str] = None
    raw_code: Optional[str] = None
    repository: Optional[str] = None
    module: Optional[str] = None
    package: Optional[str] = None


class TraceNodeSchema(BaseModel):
    node_id: str
    label: str
    node_type: str
    transformation_type: Optional[str] = None
    evidence: EvidenceSchema
    conditions: List[Dict[str, Any]] = Field(default_factory=list)


class TraceEdgeSchema(BaseModel):
    source_id: str
    target_id: str
    relation: str
    label: Optional[str] = None


class BranchSchema(BaseModel):
    branch_id: str
    condition: str
    outcome: Optional[str] = None
    node_ids: List[str] = Field(default_factory=list)


class SummarySchema(BaseModel):
    field_name: str
    origin: str
    total_nodes: int
    branch_count: int
    has_xslt: bool
    has_java: bool
    pipeline_steps: List[str]
    business_explanation: str
    technical_explanation: str


# ── Response schemas ──────────────────────────────────────────────────────────

class ScanResponse(BaseModel):
    """Response from POST /api/lineage/scan."""
    trace_id: str
    field_name: str
    summary: SummarySchema
    nodes: List[TraceNodeSchema]
    edges: List[TraceEdgeSchema]
    branches: List[BranchSchema]
    pipeline_json: Dict[str, Any]
    branch_json: Dict[str, Any]
    graph_json: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeriveResponse(BaseModel):
    """Response from POST /api/lineage/derive."""
    trace_id: str
    field_name: str
    prompt_name: str
    derivation: str
    model: str = "stub"


class ExportResponse(BaseModel):
    """Response from GET /api/lineage/export."""
    field_name: str
    format: str
    content_type: str
    file_path: Optional[str] = None
    content: Optional[str] = None


class PromptListResponse(BaseModel):
    prompts: List[str]
