"""Builds Evidence objects from parsed Java and XSLT data."""
from __future__ import annotations
from typing import Optional
from modules.trace_core.models.common import Evidence, TransformationType
from modules.trace_core.models.java_models import JavaClass, JavaMethod
from modules.trace_core.models.xslt_models import XsltTemplate


class EvidenceBuilder:
    """Constructs Evidence instances from source metadata."""

    @staticmethod
    def from_java_method(
        cls: JavaClass,
        method: JavaMethod,
        transformation_type: Optional[TransformationType] = None,
        condition_text: Optional[str] = None,
    ) -> Evidence:
        snippet = method.body_text[:300].strip() if method.body_text else None
        return Evidence(
            repository=cls.repository,
            module=cls.module,
            package=cls.package,
            class_or_template=cls.simple_name,
            method_or_template_name=method.name,
            file_path=cls.file_path,
            line_number=method.line_start,
            line_range=(method.line_start, method.line_end),
            transformation_type=transformation_type,
            condition_text=condition_text,
            raw_code=snippet,
        )

    @staticmethod
    def from_xslt_template(
        tmpl: XsltTemplate,
        transformation_type: Optional[TransformationType] = None,
        condition_text: Optional[str] = None,
    ) -> Evidence:
        snippet = (tmpl.raw_xml or "")[:300]
        return Evidence(
            repository=tmpl.repository,
            module=tmpl.module,
            class_or_template=tmpl.name,
            method_or_template_name=tmpl.name,
            file_path=tmpl.file_path,
            line_number=tmpl.line_start or None,
            transformation_type=transformation_type,
            condition_text=condition_text,
            raw_code=snippet,
        )
