"""Shared enums and base types for the Data Lineage Platform."""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Tuple


class TransformationType(str, Enum):
    EXTRACTION = "EXTRACTION"
    MAPPING = "MAPPING"
    ENRICHMENT = "ENRICHMENT"
    OVERRIDE = "OVERRIDE"
    DEFAULTING = "DEFAULTING"
    PASS_THROUGH = "PASS_THROUGH"
    CONDITIONAL_ASSIGNMENT = "CONDITIONAL_ASSIGNMENT"
    FINAL_REPORT_ASSIGNMENT = "FINAL_REPORT_ASSIGNMENT"


class OriginType(str, Enum):
    XSLT = "XSLT"
    JAVA = "JAVA"
    XSLT_THEN_JAVA = "XSLT_THEN_JAVA"
    UNKNOWN = "UNKNOWN"


class EdgeRelationType(str, Enum):
    CALLS = "CALLS"
    ASSIGNS = "ASSIGNS"
    OVERRIDES = "OVERRIDES"
    FLOWS_TO = "FLOWS_TO"
    CONDITION_TRUE = "CONDITION_TRUE"
    CONDITION_FALSE = "CONDITION_FALSE"
    IMPORTS = "IMPORTS"
    INCLUDES = "INCLUDES"


@dataclass
class Evidence:
    """Evidence metadata attached to every lineage node."""
    repository: Optional[str] = None
    module: Optional[str] = None
    package: Optional[str] = None
    class_or_template: Optional[str] = None
    method_or_template_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    line_range: Optional[Tuple[int, int]] = None
    transformation_type: Optional[TransformationType] = None
    condition_text: Optional[str] = None
    raw_code: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "repository": self.repository,
            "module": self.module,
            "package": self.package,
            "class_or_template": self.class_or_template,
            "method_or_template_name": self.method_or_template_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_range": list(self.line_range) if self.line_range else None,
            "transformation_type": self.transformation_type.value if self.transformation_type else None,
            "condition_text": self.condition_text,
            "raw_code": self.raw_code,
        }
