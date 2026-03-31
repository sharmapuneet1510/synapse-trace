"""Maven POM scanner."""
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from trace_core.logging.logger_factory import LoggerFactory

logger = LoggerFactory.get("scanner")

NS = {"m": "http://maven.apache.org/POM/4.0.0"}


@dataclass
class MavenDependency:
    group_id: str
    artifact_id: str
    version: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class MavenModule:
    pom_path: str
    group_id: Optional[str]
    artifact_id: Optional[str]
    version: Optional[str]
    modules: List[str] = field(default_factory=list)
    dependencies: List[MavenDependency] = field(default_factory=list)
    source_dirs: List[str] = field(default_factory=list)
    resource_dirs: List[str] = field(default_factory=list)

    @property
    def base_dir(self) -> str:
        return os.path.dirname(self.pom_path)

    @property
    def coordinates(self) -> str:
        return f"{self.group_id}:{self.artifact_id}:{self.version}"


def _text(el, tag: str, ns: dict) -> Optional[str]:
    node = el.find(tag, ns)
    return node.text.strip() if node is not None and node.text else None


class MavenScanner:
    """Parses pom.xml files and extracts Maven module metadata."""

    def scan_pom(self, pom_path: str) -> Optional[MavenModule]:
        """Parse a single pom.xml and return a MavenModule.

        Handles common real-world issues:
        - File not found
        - Empty file (0 bytes or only whitespace) — skipped with a warning
        - UTF-8 BOM and Windows CR/LF line endings stripped before parsing
        - Malformed XML — logged at WARNING level and skipped (not ERROR)
        """
        if not os.path.isfile(pom_path):
            logger.warning(f"pom.xml not found: {pom_path}")
            return None

        # ── Read and validate content before handing to the XML parser ────────
        try:
            raw = open(pom_path, "rb").read()
        except OSError as exc:
            logger.warning(f"Cannot read POM {pom_path}: {exc}")
            return None

        if not raw or not raw.strip():
            logger.warning(f"Skipping empty POM: {pom_path}")
            return None

        # Strip UTF-8 BOM if present (check prefix, not lstrip, to avoid
        # accidentally removing valid leading bytes that share the same value)
        content = raw[3:] if raw[:3] == b"\xef\xbb\xbf" else raw
        try:
            xml_text = content.decode("utf-8")
        except UnicodeDecodeError:
            xml_text = content.decode("latin-1", errors="replace")

        # Normalise Windows CR/LF → LF so the XML parser sees clean input
        xml_text = xml_text.replace("\r\n", "\n").replace("\r", "\n")

        try:
            root = ET.fromstring(xml_text)

            # Handle both namespaced and bare poms
            ns = NS if root.tag.startswith("{") else {}
            prefix = "m:" if ns else ""

            group_id = _text(root, f"{prefix}groupId", ns)
            artifact_id = _text(root, f"{prefix}artifactId", ns)
            version = _text(root, f"{prefix}version", ns)

            modules = []
            mods_el = root.find(f"{prefix}modules", ns)
            if mods_el is not None:
                for m in mods_el.findall(f"{prefix}module", ns):
                    if m.text:
                        modules.append(m.text.strip())

            dependencies = []
            deps_el = root.find(f"{prefix}dependencies", ns)
            if deps_el is not None:
                for dep in deps_el.findall(f"{prefix}dependency", ns):
                    gid = _text(dep, f"{prefix}groupId", ns) or ""
                    aid = _text(dep, f"{prefix}artifactId", ns) or ""
                    ver = _text(dep, f"{prefix}version", ns)
                    scope = _text(dep, f"{prefix}scope", ns)
                    dependencies.append(MavenDependency(gid, aid, ver, scope))

            base = os.path.dirname(pom_path)
            src_dir = os.path.join(base, "src", "main", "java")
            res_dir = os.path.join(base, "src", "main", "resources")
            source_dirs = [src_dir] if os.path.isdir(src_dir) else []
            resource_dirs = [res_dir] if os.path.isdir(res_dir) else []

            logger.debug(f"Parsed POM: {pom_path} -> {group_id}:{artifact_id}:{version}")
            return MavenModule(
                pom_path=pom_path,
                group_id=group_id,
                artifact_id=artifact_id,
                version=version,
                modules=modules,
                dependencies=dependencies,
                source_dirs=source_dirs,
                resource_dirs=resource_dirs,
            )

        except ET.ParseError as exc:
            logger.warning(f"Skipping malformed POM {pom_path}: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error parsing POM {pom_path}: {exc}", exc_info=True)
            return None

    def scan_all(self, pom_paths: List[str]) -> List[MavenModule]:
        """Parse multiple pom.xml files."""
        results = []
        for p in pom_paths:
            m = self.scan_pom(p)
            if m:
                results.append(m)
        return results
