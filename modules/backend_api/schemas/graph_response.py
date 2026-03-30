"""Graph-specific response schemas."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class GraphNodeSchema(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}


class GraphEdgeSchema(BaseModel):
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = {}


class GraphResponse(BaseModel):
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]
    metadata: Dict[str, Any] = {}


class PipelineStepSchema(BaseModel):
    step_id: str
    order: int
    label: str
    type: str
    transformation_type: Optional[str] = None
    evidence: Dict[str, Any] = {}


class PipelineResponse(BaseModel):
    trace_id: str
    field_name: str
    steps: List[PipelineStepSchema]
    total_steps: int


class BranchSchema(BaseModel):
    branch_id: str
    condition: str
    outcome: Optional[str] = None
    node_count: int
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []


class BranchResponse(BaseModel):
    trace_id: str
    field_name: str
    branch_count: int
    branches: List[BranchSchema]
