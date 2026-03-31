"""Main Java file parser."""
import os
from typing import Optional
from trace_core.models.java_models import JavaClass, JavaMethod
from trace_core.logging.logger_factory import LoggerFactory
from trace_core.utils.file_utils import read_file_safe
from .ast_extractor import AstExtractor
from .method_call_extractor import MethodCallExtractor
from .assignment_extractor import AssignmentExtractor
from .condition_extractor import ConditionExtractor
from .return_extractor import ReturnExtractor

logger = LoggerFactory.get("parser")


class JavaParser:
    """Parses Java source files into JavaClass models."""

    def __init__(self):
        self._ast = AstExtractor()
        self._calls = MethodCallExtractor()
        self._assigns = AssignmentExtractor()
        self._conditions = ConditionExtractor()
        self._returns = ReturnExtractor()

    def parse_file(
        self,
        path: str,
        repository: Optional[str] = None,
        module: Optional[str] = None,
        field_name: Optional[str] = None,
    ) -> Optional[JavaClass]:
        """Parse a .java file and return a JavaClass model."""
        source = read_file_safe(path)
        if source is None:
            logger.warning(f"Cannot read Java file: {path}", extra={"class_name": path})
            return None

        try:
            ast = self._ast.extract(source)
        except Exception as exc:
            logger.error(f"AST extraction failed for {path}: {exc}", exc_info=True)
            return None

        package = ast.get("package") or ""
        class_name = ast.get("class_name") or os.path.splitext(os.path.basename(path))[0]
        imports = ast.get("imports", [])
        fqn = f"{package}.{class_name}" if package else class_name

        methods: list = []
        for m in ast.get("methods", []):
            method_calls = self._calls.extract(m["body"], m["line_start"])
            assignments = self._assigns.extract(m["body"], field_name or "") if field_name else []
            conditions = self._conditions.extract(m["body"])
            method = JavaMethod(
                name=m["name"],
                class_fqn=fqn,
                return_type=m.get("return_type"),
                parameters=m.get("parameters", []),
                body_text=m["body"],
                line_start=m["line_start"],
                line_end=m["line_end"],
                method_calls=method_calls,
                assignments=assignments,
                conditions=conditions,
            )
            methods.append(method)

        java_class = JavaClass(
            fqn=fqn,
            simple_name=class_name,
            package=package,
            file_path=path,
            repository=repository,
            module=module,
            methods=methods,
            imports=imports,
        )
        logger.debug(
            f"Parsed Java class: {fqn} ({len(methods)} methods)",
            extra={"class_name": fqn, "repository": repository},
        )
        return java_class
