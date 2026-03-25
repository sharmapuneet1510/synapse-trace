"""Regex-based Java source parser for method calls, DTO unmarshalling, field mappings,
constant references (e.g. MessageKey.N_EFFECTIVE_DATE), string literals, and XSLT file references."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from orchestrator import live_events
from orchestrator.models import JavaFinding, NodeMeta

logger = logging.getLogger(__name__)


class JavaParser:
    """Parses Java source files to extract lineage-relevant findings."""

    _RE_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;")
    _RE_CLASS = re.compile(
        r"(?:public|private|protected)?\s*(?:abstract\s+)?class\s+(\w+)"
    )
    _RE_METHOD_DECL = re.compile(
        r"(?:public|private|protected)\s+[\w<>\[\],\s]+\s+(\w+)\s*\("
    )
    _RE_METHOD_CALL = re.compile(r"(\w+)\s*\.\s*(\w+)\s*\(")
    _RE_UNMARSHAL = re.compile(
        r"(?:unmarshal|readValue|fromJson|deserialize)\s*\([^)]*,\s*(\w+)\.class\)"
    )
    _RE_FIELD_MAPPING = re.compile(
        r"(\w+)\s*\.\s*set(\w+)\s*\(\s*(\w+)\s*\.\s*get(\w+)\s*\(\s*\)\s*\)"
    )
    # Constant reference: ClassName.UPPER_CASE_NAME (at least 2 uppercase segments)
    _RE_CONSTANT_REF = re.compile(
        r"(\w+)\s*\.\s*([A-Z][A-Z0-9_]{2,})"
    )
    # String literals that look like field keys: uppercase with underscores, >= 3 chars
    _RE_STRING_KEY = re.compile(r'"([A-Z][A-Z0-9_]{2,})"')

    # XSLT file references in Java code
    _RE_XSLT_REF = re.compile(r'["\']([^"\']*\.xslt?)["\']')
    _RE_TRANSFORMER_CALL = re.compile(
        r"(?:newTransformer|newTemplates|transform)\s*\("
    )

    _RE_STRING_LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')
    _RE_SINGLE_COMMENT = re.compile(r"//.*$", re.MULTILINE)
    _RE_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

    def __init__(self, repo_name: str = "") -> None:
        self._repo_name = repo_name

    def parse_file(self, file_path: Path) -> list[JavaFinding]:
        logger.info("Parsing Java file: %s (repo=%s)", file_path, self._repo_name)
        live_events.emit(live_events.PARSE_START, {"file": str(file_path), "parser": "java", "repo": self._repo_name})
        text = file_path.read_text(errors="replace")
        raw_lines = text.splitlines()

        # Strip comments for brace/pattern analysis but keep string literals
        # in a separate pass so we can extract them
        cleaned_no_comments = self._RE_BLOCK_COMMENT.sub("", text)
        cleaned_no_comments = self._RE_SINGLE_COMMENT.sub("", cleaned_no_comments)
        # Fully cleaned (no strings) for brace counting and structural patterns
        cleaned = self._RE_STRING_LITERAL.sub('""', cleaned_no_comments)
        lines = cleaned.splitlines()
        # Lines with strings preserved for literal extraction
        lines_with_strings = cleaned_no_comments.splitlines()

        findings: list[JavaFinding] = []
        current_package = ""
        current_class = ""
        current_method: str | None = None
        brace_depth = 0
        method_brace_depth = -1

        for i, line in enumerate(lines):
            lineno = i + 1
            raw_line = raw_lines[i] if i < len(raw_lines) else line
            line_with_strings = lines_with_strings[i] if i < len(lines_with_strings) else line

            # Track package
            m = self._RE_PACKAGE.match(line)
            if m:
                current_package = m.group(1)

            # Track class
            m = self._RE_CLASS.search(line)
            if m:
                current_class = m.group(1)

            # Track method entry
            m = self._RE_METHOD_DECL.search(line)
            if m and current_method is None:
                current_method = m.group(1)
                method_brace_depth = brace_depth

            # Brace counting
            brace_depth += line.count("{") - line.count("}")

            # Track method exit
            if current_method and brace_depth <= method_brace_depth:
                current_method = None
                method_brace_depth = -1

            fqcn = f"{current_package}.{current_class}" if current_package else current_class
            meta = NodeMeta(
                file_path=str(file_path),
                line_number=lineno,
                code_snippet=raw_line.strip(),
            )

            # Unmarshal detection
            m = self._RE_UNMARSHAL.search(line)
            if m:
                logger.debug("  Line %d: unmarshal -> %s found in %s.%s()", lineno, m.group(1), fqcn, current_method)
                findings.append(
                    JavaFinding(
                        class_name=fqcn,
                        method_name=current_method,
                        field_name=None,
                        finding_type="unmarshal",
                        target_class=m.group(1),
                        target_field=None,
                        meta=meta,
                        repo_name=self._repo_name,
                    )
                )

            # Field mapping detection: target.setFoo(source.getFoo())
            for m in self._RE_FIELD_MAPPING.finditer(line):
                target_var, target_field, source_var, source_field = (
                    m.group(1), m.group(2), m.group(3), m.group(4),
                )
                logger.debug("  Line %d: field_mapping %s.get%s() -> %s.set%s() in %s.%s()",
                             lineno, source_var, source_field, target_var, target_field, fqcn, current_method)
                findings.append(
                    JavaFinding(
                        class_name=fqcn,
                        method_name=current_method,
                        field_name=source_field,
                        finding_type="field_mapping",
                        target_class=target_var,
                        target_field=target_field,
                        meta=meta,
                        repo_name=self._repo_name,
                    )
                )

            # Constant reference: MessageKey.N_EFFECTIVE_DATE, FieldNames.COUNTERPARTY_ID, etc.
            for m in self._RE_CONSTANT_REF.finditer(line):
                qualifier, const_name = m.group(1), m.group(2)
                # Skip common false positives
                if qualifier in (
                    "System", "Math", "Integer", "Long", "Double", "String",
                    "Boolean", "Object", "Class", "Thread", "Runtime",
                    "Collections", "Arrays", "Optional",
                ):
                    continue
                logger.debug("  Line %d: constant_ref %s.%s found in %s.%s()", lineno, qualifier, const_name, fqcn, current_method)
                findings.append(
                    JavaFinding(
                        class_name=fqcn,
                        method_name=current_method,
                        field_name=const_name,
                        finding_type="constant_ref",
                        target_class=qualifier,
                        target_field=const_name,
                        meta=meta,
                        repo_name=self._repo_name,
                    )
                )

            # String literals that look like field keys: "N_EFFECTIVE_DATE", "COUNTERPARTY_ID"
            for m in self._RE_STRING_KEY.finditer(line_with_strings):
                key_value = m.group(1)
                logger.debug("  Line %d: string_literal \"%s\" found in %s.%s()", lineno, key_value, fqcn, current_method)
                findings.append(
                    JavaFinding(
                        class_name=fqcn,
                        method_name=current_method,
                        field_name=key_value,
                        finding_type="string_literal",
                        target_class=None,
                        target_field=key_value,
                        meta=meta,
                        repo_name=self._repo_name,
                    )
                )

            # XSLT file references: "trade_transform.xsl", StreamSource("foo.xsl")
            for m in self._RE_XSLT_REF.finditer(line_with_strings):
                xslt_path = m.group(1)
                xslt_name = Path(xslt_path).stem
                logger.debug("  Line %d: xslt_ref '%s' (stem='%s') found in %s.%s()", lineno, xslt_path, xslt_name, fqcn, current_method)
                findings.append(
                    JavaFinding(
                        class_name=fqcn,
                        method_name=current_method,
                        field_name=xslt_name,
                        finding_type="xslt_ref",
                        target_class=None,
                        target_field=xslt_path,
                        meta=meta,
                        repo_name=self._repo_name,
                    )
                )

            # Transformer calls: newTransformer(), transform() — marks the method as doing XSLT processing
            if self._RE_TRANSFORMER_CALL.search(line):
                findings.append(
                    JavaFinding(
                        class_name=fqcn,
                        method_name=current_method,
                        field_name=None,
                        finding_type="method_call",
                        target_class="Transformer",
                        target_field="transform",
                        meta=meta,
                        repo_name=self._repo_name,
                    )
                )

            # Generic method call detection (lower priority)
            for m in self._RE_METHOD_CALL.finditer(line):
                obj_name, method_name = m.group(1), m.group(2)
                if method_name.startswith(("set", "get")):
                    continue
                if obj_name in ("System", "log", "logger", "LOG", "LOGGER"):
                    continue
                logger.debug("  Line %d: method_call %s.%s() found in %s.%s()", lineno, obj_name, method_name, fqcn, current_method)
                findings.append(
                    JavaFinding(
                        class_name=fqcn,
                        method_name=current_method,
                        field_name=None,
                        finding_type="method_call",
                        target_class=obj_name,
                        target_field=method_name,
                        meta=meta,
                        repo_name=self._repo_name,
                    )
                )

        logger.info("  Parsed %s: %d findings", file_path.name, len(findings))
        live_events.emit(live_events.PARSE_COMPLETE, {
            "file": str(file_path), "parser": "java",
            "findings": len(findings), "repo": self._repo_name,
        })
        return findings

    def parse_directory(self, dir_path: Path) -> list[JavaFinding]:
        logger.info("Parsing Java directory: %s", dir_path)
        findings: list[JavaFinding] = []
        java_files = sorted(dir_path.rglob("*.java"))
        logger.info("  Found %d Java files in %s", len(java_files), dir_path)
        for java_file in java_files:
            findings.extend(self.parse_file(java_file))
        logger.info("  Total Java findings from %s: %d", dir_path, len(findings))
        return findings
