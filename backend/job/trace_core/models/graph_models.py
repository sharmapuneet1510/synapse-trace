"""Graph export models for the Data Lineage Platform."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class GraphNode:
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "type": self.type, "properties": self.properties}


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "relation": self.relation, "properties": self.properties}


@dataclass
class GraphExport:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }
