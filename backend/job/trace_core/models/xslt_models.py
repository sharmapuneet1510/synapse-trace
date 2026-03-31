"""XSLT AST models for the Data Lineage Platform."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class XsltVariable:
    name: str
    select: Optional[str]
    content: Optional[str]
    line_number: int

    def to_dict(self) -> dict:
        return {"name": self.name, "select": self.select, "content": self.content, "line_number": self.line_number}


@dataclass
class XsltParam:
    name: str
    select: Optional[str]
    line_number: int

    def to_dict(self) -> dict:
        return {"name": self.name, "select": self.select, "line_number": self.line_number}


@dataclass
class XsltCallTemplate:
    name: str
    params: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0

    def to_dict(self) -> dict:
        return {"name": self.name, "params": self.params, "line_number": self.line_number}


@dataclass
class XsltApplyTemplates:
    select: Optional[str]
    mode: Optional[str]
    line_number: int = 0

    def to_dict(self) -> dict:
        return {"select": self.select, "mode": self.mode, "line_number": self.line_number}


@dataclass
class XsltCondition:
    test: str
    type: str  # xsl:if or xsl:when
    line_number: int

    def to_dict(self) -> dict:
        return {"test": self.test, "type": self.type, "line_number": self.line_number}


@dataclass
class XsltOutputMapping:
    field_name: str
    xpath_expression: str
    line_number: int

    def to_dict(self) -> dict:
        return {"field_name": self.field_name, "xpath_expression": self.xpath_expression, "line_number": self.line_number}


@dataclass
class XsltTemplate:
    name: str
    file_path: str
    repository: Optional[str] = None
    module: Optional[str] = None
    match: Optional[str] = None
    variables: List[XsltVariable] = field(default_factory=list)
    params: List[XsltParam] = field(default_factory=list)
    call_templates: List[XsltCallTemplate] = field(default_factory=list)
    apply_templates: List[XsltApplyTemplates] = field(default_factory=list)
    conditions: List[XsltCondition] = field(default_factory=list)
    output_mappings: List[XsltOutputMapping] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    raw_xml: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "match": self.match,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "variables": [v.to_dict() for v in self.variables],
            "params": [p.to_dict() for p in self.params],
            "call_templates": [c.to_dict() for c in self.call_templates],
            "apply_templates": [a.to_dict() for a in self.apply_templates],
            "conditions": [c.to_dict() for c in self.conditions],
            "output_mappings": [o.to_dict() for o in self.output_mappings],
        }


@dataclass
class XsltFile:
    file_path: str
    repository: Optional[str] = None
    module: Optional[str] = None
    templates: List[XsltTemplate] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    global_variables: List[XsltVariable] = field(default_factory=list)
    global_params: List[XsltParam] = field(default_factory=list)

    def get_template(self, name: str) -> Optional[XsltTemplate]:
        for t in self.templates:
            if t.name == name:
                return t
        return None
