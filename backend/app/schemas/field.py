from __future__ import annotations

from pydantic import BaseModel


class XPathEntry(BaseModel):
    name: str
    source: str
    xpath: str
    template: str | None = None
    output_element: str | None = None
    line: int | None = None


class DependencyRef(BaseModel):
    field_name: str
    relationship: str
    source_type: str
    file_path: str | None = None
    line_number: int | None = None


class JavaReference(BaseModel):
    class_name: str
    method_name: str | None = None
    finding_type: str
    code_snippet: str | None = None
    file_path: str | None = None
    line_number: int | None = None


class FieldDetail(BaseModel):
    jurisdiction_id: str
    field_name: str
    header: str
    asset_classes: list[str]
    config_type: str
    xslt_logic: str | None = None
    xslt_file: str | None = None
    xslt_line: int | None = None
    input_xpaths: list[XPathEntry] = []
    dependencies: list[DependencyRef] = []
    java_references: list[JavaReference] = []
