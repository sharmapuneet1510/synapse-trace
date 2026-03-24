"""Core data models for Synapse Trace lineage analysis."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class EdgeType(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    CALLS = "CALLS"
    TRANSFORMS = "TRANSFORMS"
    UNMARSHALS_TO = "UNMARSHALS_TO"
    CROSS_REPO = "CROSS_REPO"
    LOADS_XSLT = "LOADS_XSLT"


class NodeType(str, Enum):
    JAVA_CLASS = "JAVA_CLASS"
    JAVA_METHOD = "JAVA_METHOD"
    JAVA_FIELD = "JAVA_FIELD"
    JAVA_CONSTANT = "JAVA_CONSTANT"
    DTO = "DTO"
    XSLT_FILE = "XSLT_FILE"
    XSLT_TEMPLATE = "XSLT_TEMPLATE"
    XSLT_FIELD = "XSLT_FIELD"


@dataclass(slots=True)
class NodeMeta:
    """FR-G2: Rich metadata — file path, line number, code snippet, MD5 hash."""

    file_path: str
    line_number: int
    code_snippet: str
    md5_hash: str = ""

    def __post_init__(self) -> None:
        if not self.md5_hash:
            self.md5_hash = hashlib.md5(self.code_snippet.encode()).hexdigest()


@dataclass(slots=True)
class LineageNode:
    id: str
    label: str
    node_type: NodeType
    meta: NodeMeta
    properties: dict = field(default_factory=dict)


@dataclass(slots=True)
class LineageEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: dict = field(default_factory=dict)


@dataclass
class RepoConfig:
    """Configuration for a single repository / module.

    Supports three modes:
      - scan_dirs: auto-discover .java and .xsl/.xslt files (recommended)
      - java_dirs + xslt_dirs: explicit separation (legacy)
      - Both: scan_dirs are auto-detected, explicit dirs are added on top
    """

    name: str
    path: Path
    scan_dirs: list[Path] = field(default_factory=list)
    java_dirs: list[Path] = field(default_factory=list)
    xslt_dirs: list[Path] = field(default_factory=list)

    def resolve_dirs(self) -> None:
        """Resolve relative dirs against the repo path."""
        self.scan_dirs = [
            d if d.is_absolute() else self.path / d for d in self.scan_dirs
        ]
        self.java_dirs = [
            d if d.is_absolute() else self.path / d for d in self.java_dirs
        ]
        self.xslt_dirs = [
            d if d.is_absolute() else self.path / d for d in self.xslt_dirs
        ]


@dataclass(slots=True)
class JavaFinding:
    class_name: str
    method_name: Optional[str]
    field_name: Optional[str]
    finding_type: str  # "method_call" | "unmarshal" | "field_mapping" | "constant_ref" | "string_literal" | "xslt_ref"
    target_class: Optional[str]
    target_field: Optional[str]
    meta: NodeMeta
    repo_name: str = ""


@dataclass(slots=True)
class XsltFinding:
    template_name: str
    template_match: str
    field_source: Optional[str]
    field_target: Optional[str]
    finding_type: str  # "value_of" | "template_call" | "field_mapping"
    meta: NodeMeta
    repo_name: str = ""


@dataclass
class StitchedLineage:
    """Complete lineage graph produced by the Stitcher."""

    nodes: list[LineageNode] = field(default_factory=list)
    edges: list[LineageEdge] = field(default_factory=list)
