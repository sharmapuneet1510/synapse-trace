"""Schemas for variable trace API."""
from __future__ import annotations
from pydantic import BaseModel


class TraceRequest(BaseModel):
    variable_name: str
    jurisdiction_id: str
    # Extra name variations the user wants to include in the search
    additional_variations: list[str] = []
    max_depth: int = 15


class TraceNode(BaseModel):
    id: str
    label: str
    node_type: str
    file_path: str | None = None
    line_number: int | None = None
    code_snippet: str | None = None
    properties: dict = {}


class TraceEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: dict = {}


class TraceResponse(BaseModel):
    variable_name: str
    jurisdiction_id: str
    # All name variations that were searched (auto-generated + user-provided)
    variations_searched: list[str]
    nodes: list[TraceNode]
    edges: list[TraceEdge]
    node_count: int
    edge_count: int
    parse_status: str  # "ready" | "pending" | "not_parsed"
