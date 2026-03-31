"""Trace result models for the Data Lineage Platform."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .common import TransformationType, OriginType, EdgeRelationType, Evidence


@dataclass
class TraceNode:
    node_id: str
    label: str
    node_type: str  # java_method | xslt_template | field | condition | origin
    evidence: Evidence
    transformation_type: Optional[TransformationType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "transformation_type": self.transformation_type.value if self.transformation_type else None,
            "evidence": self.evidence.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class TraceEdge:
    source_id: str
    target_id: str
    relation: EdgeRelationType
    condition_text: Optional[str] = None
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.value,
            "condition_text": self.condition_text,
            "label": self.label or self.relation.value,
        }


@dataclass
class BranchPath:
    branch_id: str
    condition: str
    nodes: List[TraceNode] = field(default_factory=list)
    edges: List[TraceEdge] = field(default_factory=list)
    outcome: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "branch_id": self.branch_id,
            "condition": self.condition,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "outcome": self.outcome,
        }


@dataclass
class TraceSummary:
    field_name: str
    origin: OriginType
    pipeline_steps: List[str]
    branch_count: int
    total_nodes: int
    has_xslt: bool
    has_java: bool
    technical_explanation: str
    business_explanation: str

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "origin": self.origin.value,
            "pipeline_steps": self.pipeline_steps,
            "branch_count": self.branch_count,
            "total_nodes": self.total_nodes,
            "has_xslt": self.has_xslt,
            "has_java": self.has_java,
            "technical_explanation": self.technical_explanation,
            "business_explanation": self.business_explanation,
        }
