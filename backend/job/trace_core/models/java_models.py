"""Java AST models for the Data Lineage Platform."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
from .common import TransformationType


@dataclass
class MethodCall:
    callee_class: Optional[str]
    callee_method: str
    arguments: List[str]
    line_number: int
    raw_expression: str

    def to_dict(self) -> dict:
        return {
            "callee_class": self.callee_class,
            "callee_method": self.callee_method,
            "arguments": self.arguments,
            "line_number": self.line_number,
            "raw_expression": self.raw_expression,
        }


@dataclass
class Assignment:
    target_field: str
    source_expression: str
    line_number: int
    transformation_type: Optional[TransformationType] = None

    def to_dict(self) -> dict:
        return {
            "target_field": self.target_field,
            "source_expression": self.source_expression,
            "line_number": self.line_number,
            "transformation_type": self.transformation_type.value if self.transformation_type else None,
        }


@dataclass
class Condition:
    condition_text: str
    branch_type: str  # if / else / switch / ternary
    line_number: int
    true_branch: Optional[str] = None
    false_branch: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "condition_text": self.condition_text,
            "branch_type": self.branch_type,
            "line_number": self.line_number,
            "true_branch": self.true_branch,
            "false_branch": self.false_branch,
        }


@dataclass
class JavaMethod:
    name: str
    class_fqn: str
    return_type: Optional[str]
    parameters: List[str]
    body_text: str
    line_start: int
    line_end: int
    method_calls: List[MethodCall] = field(default_factory=list)
    assignments: List[Assignment] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)

    @property
    def signature(self) -> str:
        return f"{self.class_fqn}.{self.name}({', '.join(self.parameters)})"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "class_fqn": self.class_fqn,
            "return_type": self.return_type,
            "parameters": self.parameters,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "method_calls": [c.to_dict() for c in self.method_calls],
            "assignments": [a.to_dict() for a in self.assignments],
            "conditions": [c.to_dict() for c in self.conditions],
        }


@dataclass
class JavaClass:
    fqn: str  # fully qualified name e.g. com.xxx.trade.TradeService
    simple_name: str
    package: str
    file_path: str
    repository: Optional[str] = None
    module: Optional[str] = None
    methods: List[JavaMethod] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

    def get_method(self, name: str) -> Optional[JavaMethod]:
        for m in self.methods:
            if m.name == name:
                return m
        return None

    def to_dict(self) -> dict:
        return {
            "fqn": self.fqn,
            "simple_name": self.simple_name,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "method_count": len(self.methods),
        }
