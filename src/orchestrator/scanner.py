"""Module scanner — auto-discovers source files and detects cross-language references.

Given a directory, the scanner:
  1. Discovers module boundaries (pom.xml, build.gradle, or src/main layout)
  2. Recursively finds all .java and .xsl/.xslt files per module
  3. Detects how Java code references XSLT files (transformer loads, resource paths)
  4. Resolves XSLT filenames to actual file paths on disk
  5. Returns ScannedModule / ScannedProject with grouped files and cross-language references

Supports multi-project, multi-module structures like:
  project-a/
    module-1/pom.xml + src/main/java/...
    module-2/pom.xml + src/main/resources/xslt/...
  project-b/
    module-3/build.gradle + src/...
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from orchestrator import live_events

logger = logging.getLogger(__name__)


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


@dataclass
class ScannedProject:
    """Result of scanning a project root that may contain multiple modules."""

    name: str
    root: Path
    modules: list[ScannedModule] = field(default_factory=list)

    @property
    def total_java(self) -> int:
        return sum(len(m.java_files) for m in self.modules)

    @property
    def total_xslt(self) -> int:
        return sum(len(m.xslt_files) for m in self.modules)

    @property
    def total_refs(self) -> int:
        return sum(len(m.xslt_refs) for m in self.modules)

    def summary(self) -> str:
        return (
            f"{self.name}: {len(self.modules)} modules, "
            f"{self.total_java} java, {self.total_xslt} xslt, "
            f"{self.total_refs} cross-language refs"
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


# Build-tool markers that indicate a module boundary
_MODULE_MARKERS = ("pom.xml", "build.gradle", "build.gradle.kts")


class ModuleScanner:
    """Scans a directory tree to discover source files and cross-language references.

    Supports:
      - Single module scan: scan(root)
      - Multi-module project: scan_project(root) auto-discovers modules
      - Multi-dir merge: scan_multiple(dirs)
    """

    def scan_project(self, root: Path, name: str = "") -> ScannedProject:
        """Scan a project root, auto-discover modules, and scan each one.

        Module discovery order:
          1. Look for sub-directories with build markers (pom.xml, build.gradle)
          2. If none found, treat the root itself as a single module
        """
        if not name:
            name = root.name

        logger.info("Scanning project '%s' at %s", name, root)
        live_events.emit(live_events.SCAN_START, {"name": name, "root": str(root), "type": "project"})
        project = ScannedProject(name=name, root=root)
        module_dirs = self.discover_modules(root)

        if not module_dirs:
            logger.info("No sub-modules found — treating root as single module")
            module = self.scan(root, name=name)
            project.modules.append(module)
        else:
            logger.info("Discovered %d module(s): %s", len(module_dirs), [d.name for d in module_dirs])
            for mod_dir in module_dirs:
                mod_name = f"{name}/{mod_dir.name}"
                module = self.scan(mod_dir, name=mod_name)
                if module.java_files or module.xslt_files:
                    project.modules.append(module)
                    logger.debug("Module '%s' included: %d java, %d xslt files", mod_name, len(module.java_files), len(module.xslt_files))
                else:
                    logger.debug("Module '%s' skipped — no source files", mod_name)

            root_module = self._scan_root_only(root, module_dirs, name=f"{name}/root")
            if root_module.java_files or root_module.xslt_files:
                project.modules.append(root_module)
                logger.debug("Root module included: %d java, %d xslt files", len(root_module.java_files), len(root_module.xslt_files))

        self._cross_resolve_xslt(project)
        logger.info("Project '%s' scan complete: %s", name, project.summary())
        live_events.emit(live_events.SCAN_COMPLETE, {
            "name": name, "modules": len(project.modules),
            "java_files": project.total_java, "xslt_files": project.total_xslt,
            "xslt_refs": project.total_refs,
        })

        return project

    @staticmethod
    def discover_modules(root: Path) -> list[Path]:
        """Find sub-module directories under a project root.

        A sub-module is a direct child directory that contains a build marker
        (pom.xml, build.gradle, build.gradle.kts) or has a src/ directory.
        The root itself is excluded.
        """
        modules: list[Path] = []
        if not root.is_dir():
            logger.warning("discover_modules: root is not a directory: %s", root)
            return modules

        logger.debug("Discovering modules under %s (markers: %s)", root, _MODULE_MARKERS)
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue

            has_marker = any((child / marker).exists() for marker in _MODULE_MARKERS)
            has_src = (child / "src").is_dir()

            if has_marker or has_src:
                reason = []
                if has_marker:
                    found_markers = [m for m in _MODULE_MARKERS if (child / m).exists()]
                    reason.append(f"markers={found_markers}")
                if has_src:
                    reason.append("has src/")
                logger.debug("  Found module: %s (%s)", child.name, ", ".join(reason))
                modules.append(child)

        return modules

    def _scan_root_only(
        self, root: Path, exclude_dirs: list[Path], name: str
    ) -> ScannedModule:
        """Scan files directly in root, excluding sub-module directories."""
        module = ScannedModule(name=name, root=root)
        exclude_set = {d.resolve() for d in exclude_dirs}

        for java_file in sorted(root.rglob("*.java")):
            if not any(java_file.resolve().is_relative_to(ex) for ex in exclude_set):
                module.java_files.append(java_file)

        for ext in ("*.xsl", "*.xslt"):
            for xslt_file in sorted(root.rglob(ext)):
                if not any(xslt_file.resolve().is_relative_to(ex) for ex in exclude_set):
                    module.xslt_files.append(xslt_file)

        # Build XSLT index and scan for refs
        module._xslt_by_name = {}
        for xf in module.xslt_files:
            module._xslt_by_name.setdefault(xf.name, []).append(xf)
        for java_file in module.java_files:
            refs = self._scan_java_for_xslt_refs(java_file, module)
            module.xslt_refs.extend(refs)

        return module

    @staticmethod
    def _cross_resolve_xslt(project: ScannedProject) -> None:
        """Re-resolve unresolved XSLT references using files from sibling modules."""
        combined_index: dict[str, list[Path]] = {}
        for mod in project.modules:
            for xf in mod.xslt_files:
                combined_index.setdefault(xf.name, []).append(xf)

        logger.debug("Cross-resolve XSLT: combined index has %d unique filenames", len(combined_index))

        for mod in project.modules:
            for ref in mod.xslt_refs:
                if ref.xslt_resolved is not None:
                    continue
                basename = Path(ref.xslt_filename).name
                candidates = combined_index.get(basename, [])
                if candidates:
                    ref.xslt_resolved = candidates[0]
                    logger.info("Cross-resolved XSLT ref '%s' in %s -> %s (from sibling module)", basename, mod.name, candidates[0])
                else:
                    logger.warning("Cross-resolve failed: '%s' referenced in %s not found in any module", basename, mod.name)

    def scan(self, root: Path, name: str = "") -> ScannedModule:
        if not name:
            name = root.name

        logger.info("Scanning module '%s' at %s", name, root)
        module = ScannedModule(name=name, root=root)

        # Step 1: Discover all source files
        module.java_files = sorted(root.rglob("*.java"))
        module.xslt_files = sorted(
            list(root.rglob("*.xsl")) + list(root.rglob("*.xslt"))
        )

        for jf in module.java_files:
            logger.debug("  Found Java file: %s", jf)
            live_events.emit(live_events.SCAN_FILE, {"file": str(jf), "type": "java", "module": name})
        for xf in module.xslt_files:
            logger.debug("  Found XSLT file: %s", xf)
            live_events.emit(live_events.SCAN_FILE, {"file": str(xf), "type": "xslt", "module": name})

        logger.info("Module '%s': discovered %d java, %d xslt files", name, len(module.java_files), len(module.xslt_files))

        # Build XSLT filename index for resolution
        module._xslt_by_name = {}
        for xf in module.xslt_files:
            module._xslt_by_name.setdefault(xf.name, []).append(xf)

        # Step 2: Scan Java files for XSLT references
        for java_file in module.java_files:
            refs = self._scan_java_for_xslt_refs(java_file, module)
            if refs:
                logger.info("  %s: found %d XSLT reference(s)", java_file.name, len(refs))
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
        logger.debug("Scanning %s for XSLT references", java_file)
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
                    logger.info("  Line %d: XSLT ref [%s] '%s' in %s.%s() -> resolved=%s",
                                lineno, ref_type, xslt_name, fqcn, current_method, resolved)
                    live_events.emit(live_events.SCAN_REF, {
                        "ref_type": ref_type, "xslt_name": xslt_name,
                        "java_class": fqcn, "method": current_method,
                        "resolved": str(resolved) if resolved else None,
                        "file": str(java_file), "line": lineno,
                    })
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
                    logger.info("  Line %d: XSLT ref [string_path] '%s' in %s.%s() -> resolved=%s",
                                lineno, xslt_name, fqcn, current_method, resolved)
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
        logger.debug("Resolving XSLT ref '%s' (basename='%s') from %s", xslt_name, basename, java_file.name)

        # 1. Basename match
        if basename in module._xslt_by_name:
            candidates = module._xslt_by_name[basename]
            logger.debug("  Strategy 1 (basename index): %d candidate(s) for '%s'", len(candidates), basename)
            if len(candidates) == 1:
                logger.debug("  Resolved via basename match -> %s", candidates[0])
                return candidates[0]
            for c in candidates:
                if xslt_name in str(c):
                    logger.debug("  Resolved via path substring match -> %s", c)
                    return c
            logger.debug("  Resolved via first candidate -> %s", candidates[0])
            return candidates[0]

        # 2. Relative to Java file
        relative = java_file.parent / xslt_name
        logger.debug("  Strategy 2 (relative to java): checking %s", relative)
        if relative.exists():
            logger.debug("  Resolved via relative path -> %s", relative.resolve())
            return relative.resolve()

        # 3. Relative to module root
        from_root = module.root / xslt_name
        logger.debug("  Strategy 3 (relative to module root): checking %s", from_root)
        if from_root.exists():
            logger.debug("  Resolved via module root -> %s", from_root.resolve())
            return from_root.resolve()

        # 4. Suffix match
        logger.debug("  Strategy 4 (suffix match): checking %d xslt files", len(module.xslt_files))
        for xf in module.xslt_files:
            if str(xf).endswith(xslt_name):
                logger.debug("  Resolved via suffix match -> %s", xf)
                return xf

        logger.warning("  Could not resolve XSLT ref '%s' in module '%s'", xslt_name, module.name)
        return None
