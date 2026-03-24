"""Module scanner — auto-discovers source files and detects cross-language references.

Given a directory, the scanner:
  1. Recursively finds all .java and .xsl/.xslt files
  2. Detects how Java code references XSLT files (transformer loads, resource paths)
  3. Resolves XSLT filenames to actual file paths on disk
  4. Returns a ScannedModule with grouped files and cross-language references
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class XsltReference:
    """A reference from Java code to an XSLT file."""

    java_file: Path
    java_class: str
    java_method: str
    xslt_filename: str          # The referenced filename (e.g. "trade_transform.xsl")
    xslt_resolved: Path | None  # Resolved path on disk, or None if not found
    line_number: int
    code_snippet: str
    ref_type: str  # "stream_source" | "resource" | "classpath" | "string_path"


@dataclass
class ScannedModule:
    """Result of scanning a module directory."""

    name: str
    root: Path
    java_files: list[Path] = field(default_factory=list)
    xslt_files: list[Path] = field(default_factory=list)
    xslt_refs: list[XsltReference] = field(default_factory=list)

    # XSLT files indexed by filename (basename) for resolution
    _xslt_by_name: dict[str, list[Path]] = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"{self.name}: {len(self.java_files)} java, "
            f"{len(self.xslt_files)} xslt, "
            f"{len(self.xslt_refs)} cross-language refs"
        )


# Regex patterns for detecting XSLT references in Java code
# StreamSource("path/to/file.xsl") or StreamSource(new File("file.xsl"))
_RE_STREAM_SOURCE = re.compile(
    r'(?:new\s+)?StreamSource\s*\(\s*(?:new\s+\w+\s*\(\s*)?["\']([^"\']*\.xslt?)["\']'
)
# getResourceAsStream("path/to/file.xsl")
_RE_GET_RESOURCE = re.compile(
    r'getResourceAsStream\s*\(\s*["\']([^"\']*\.xslt?)["\']'
)
# getResource("path/to/file.xsl")
_RE_GET_RESOURCE2 = re.compile(
    r'getResource\s*\(\s*["\']([^"\']*\.xslt?)["\']'
)
# ClassPathResource("path/to/file.xsl")
_RE_CLASSPATH = re.compile(
    r'ClassPathResource\s*\(\s*["\']([^"\']*\.xslt?)["\']'
)
# Any string literal ending in .xsl or .xslt (catch-all)
_RE_XSLT_STRING = re.compile(
    r'["\']([^"\']*\.xslt?)["\']'
)
# TransformerFactory / Templates patterns (used to detect transform calls)
_RE_TRANSFORMER = re.compile(
    r'(?:newTransformer|newTemplates)\s*\('
)

_RE_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;")
_RE_CLASS = re.compile(
    r"(?:public|private|protected)?\s*(?:abstract\s+)?class\s+(\w+)"
)
_RE_METHOD_DECL = re.compile(
    r"(?:public|private|protected)\s+[\w<>\[\],\s]+\s+(\w+)\s*\("
)


class ModuleScanner:
    """Scans a directory tree to discover source files and cross-language references."""

    def scan(self, root: Path, name: str = "") -> ScannedModule:
        if not name:
            name = root.name

        module = ScannedModule(name=name, root=root)

        # Step 1: Discover all source files
        module.java_files = sorted(root.rglob("*.java"))
        module.xslt_files = sorted(
            list(root.rglob("*.xsl")) + list(root.rglob("*.xslt"))
        )

        # Build XSLT filename index for resolution
        module._xslt_by_name = {}
        for xf in module.xslt_files:
            module._xslt_by_name.setdefault(xf.name, []).append(xf)

        # Step 2: Scan Java files for XSLT references
        for java_file in module.java_files:
            refs = self._scan_java_for_xslt_refs(java_file, module)
            module.xslt_refs.extend(refs)

        return module

    def scan_multiple(self, dirs: list[Path], name: str = "") -> ScannedModule:
        """Scan multiple directories as one logical module."""
        combined = ScannedModule(
            name=name or "combined",
            root=dirs[0] if dirs else Path("."),
        )

        for d in dirs:
            if not d.exists():
                continue
            sub = self.scan(d, name=name)
            combined.java_files.extend(sub.java_files)
            combined.xslt_files.extend(sub.xslt_files)
            combined.xslt_refs.extend(sub.xslt_refs)
            for k, v in sub._xslt_by_name.items():
                combined._xslt_by_name.setdefault(k, []).extend(v)

        return combined

    def _scan_java_for_xslt_refs(
        self, java_file: Path, module: ScannedModule
    ) -> list[XsltReference]:
        """Scan a Java file for references to XSLT files."""
        text = java_file.read_text(errors="replace")
        lines = text.splitlines()
        refs: list[XsltReference] = []

        current_package = ""
        current_class = ""
        current_method = ""

        for i, line in enumerate(lines):
            lineno = i + 1

            m = _RE_PACKAGE.match(line)
            if m:
                current_package = m.group(1)

            m = _RE_CLASS.search(line)
            if m:
                current_class = m.group(1)

            m = _RE_METHOD_DECL.search(line)
            if m:
                current_method = m.group(1)

            fqcn = f"{current_package}.{current_class}" if current_package else current_class

            # Check all XSLT reference patterns
            for pattern, ref_type in [
                (_RE_STREAM_SOURCE, "stream_source"),
                (_RE_GET_RESOURCE, "resource"),
                (_RE_GET_RESOURCE2, "resource"),
                (_RE_CLASSPATH, "classpath"),
            ]:
                for m in pattern.finditer(line):
                    xslt_name = m.group(1)
                    resolved = self._resolve_xslt(xslt_name, module, java_file)
                    refs.append(
                        XsltReference(
                            java_file=java_file,
                            java_class=fqcn,
                            java_method=current_method,
                            xslt_filename=xslt_name,
                            xslt_resolved=resolved,
                            line_number=lineno,
                            code_snippet=line.strip(),
                            ref_type=ref_type,
                        )
                    )

            # Catch-all: string literal with .xsl/.xslt (only if not already matched above)
            if not any(p.search(line) for p, _ in [
                (_RE_STREAM_SOURCE, ""), (_RE_GET_RESOURCE, ""),
                (_RE_GET_RESOURCE2, ""), (_RE_CLASSPATH, ""),
            ]):
                for m in _RE_XSLT_STRING.finditer(line):
                    xslt_name = m.group(1)
                    resolved = self._resolve_xslt(xslt_name, module, java_file)
                    refs.append(
                        XsltReference(
                            java_file=java_file,
                            java_class=fqcn,
                            java_method=current_method,
                            xslt_filename=xslt_name,
                            xslt_resolved=resolved,
                            line_number=lineno,
                            code_snippet=line.strip(),
                            ref_type="string_path",
                        )
                    )

        return refs

    @staticmethod
    def _resolve_xslt(
        xslt_name: str, module: ScannedModule, java_file: Path
    ) -> Path | None:
        """Resolve an XSLT filename reference to an actual file on disk.

        Resolution order:
          1. Exact basename match in the module's XSLT files
          2. Relative path from the Java file's directory
          3. Relative path from the module root
          4. Path suffix match (for partial paths like "xslt/trade.xsl")
        """
        basename = Path(xslt_name).name

        # 1. Basename match
        if basename in module._xslt_by_name:
            candidates = module._xslt_by_name[basename]
            if len(candidates) == 1:
                return candidates[0]
            # Multiple matches — try to pick the closest one by path
            for c in candidates:
                if xslt_name in str(c):
                    return c
            return candidates[0]

        # 2. Relative to Java file
        relative = java_file.parent / xslt_name
        if relative.exists():
            return relative.resolve()

        # 3. Relative to module root
        from_root = module.root / xslt_name
        if from_root.exists():
            return from_root.resolve()

        # 4. Suffix match
        for xf in module.xslt_files:
            if str(xf).endswith(xslt_name):
                return xf

        return None
