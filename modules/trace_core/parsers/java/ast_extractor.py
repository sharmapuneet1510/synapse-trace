"""Regex-based AST extractor for Java source files."""
import re
from typing import List, Dict, Any, Tuple, Optional


CLASS_PATTERN = re.compile(
    r"(?:public|protected|private|abstract|final|static)?\s*"
    r"(?:public|protected|private|abstract|final|static)?\s*"
    r"class\s+(\w+)\s*(?:extends\s+\w+)?\s*(?:implements\s+[\w\s,<>]+)?\s*\{"
)

PACKAGE_PATTERN = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
IMPORT_PATTERN = re.compile(r"^\s*import\s+([\w.*]+)\s*;", re.MULTILINE)

METHOD_PATTERN = re.compile(
    r"(?:(?:public|protected|private|static|final|synchronized|abstract|native|default)\s+)*"
    r"([\w<>\[\],\s?]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{",
    re.MULTILINE,
)


class AstExtractor:
    """Extracts class, method, import information from Java source text."""

    def extract(self, source: str) -> Dict[str, Any]:
        package = self._extract_package(source)
        imports = self._extract_imports(source)
        class_name = self._extract_class_name(source)
        methods = self._extract_methods(source)
        return {
            "package": package,
            "imports": imports,
            "class_name": class_name,
            "methods": methods,
        }

    def _extract_package(self, source: str) -> Optional[str]:
        m = PACKAGE_PATTERN.search(source)
        return m.group(1) if m else None

    def _extract_imports(self, source: str) -> List[str]:
        return [m.group(1) for m in IMPORT_PATTERN.finditer(source)]

    def _extract_class_name(self, source: str) -> Optional[str]:
        m = CLASS_PATTERN.search(source)
        return m.group(1) if m else None

    def _extract_methods(self, source: str) -> List[Dict[str, Any]]:
        methods = []
        lines = source.splitlines()

        # Find method signatures with brace matching
        for m in METHOD_PATTERN.finditer(source):
            return_type = m.group(1).strip()
            name = m.group(2).strip()
            params_raw = m.group(3).strip()

            if name in {"if", "while", "for", "switch", "catch", "try", "else", "class", "interface", "enum", "new"}:
                continue
            if return_type in {"class", "interface", "enum", "new"}:
                continue

            params = [p.strip() for p in params_raw.split(",") if p.strip()] if params_raw else []
            start_pos = m.start()
            brace_pos = source.index("{", m.start())
            body, end_pos = self._extract_body(source, brace_pos)
            line_start = source[:start_pos].count("\n") + 1
            line_end = source[:end_pos].count("\n") + 1

            methods.append({
                "name": name,
                "return_type": return_type,
                "parameters": params,
                "body": body,
                "line_start": line_start,
                "line_end": line_end,
            })
        return methods

    def _extract_body(self, source: str, open_brace_pos: int) -> Tuple[str, int]:
        """Extract method body by brace matching. Returns (body_text, end_position)."""
        depth = 0
        i = open_brace_pos
        in_string = False
        in_char = False
        in_line_comment = False
        in_block_comment = False
        start = open_brace_pos + 1

        while i < len(source):
            ch = source[i]
            if in_line_comment:
                if ch == "\n":
                    in_line_comment = False
            elif in_block_comment:
                if ch == "*" and i + 1 < len(source) and source[i + 1] == "/":
                    in_block_comment = False
                    i += 1
            elif in_string:
                if ch == "\\" :
                    i += 1
                elif ch == '"':
                    in_string = False
            elif in_char:
                if ch == "\\":
                    i += 1
                elif ch == "'":
                    in_char = False
            else:
                if ch == "/" and i + 1 < len(source) and source[i + 1] == "/":
                    in_line_comment = True
                elif ch == "/" and i + 1 < len(source) and source[i + 1] == "*":
                    in_block_comment = True
                elif ch == '"':
                    in_string = True
                elif ch == "'":
                    in_char = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    if depth == 0:
                        return source[start:i], i
                    depth -= 1
            i += 1

        return source[start:], len(source) - 1
