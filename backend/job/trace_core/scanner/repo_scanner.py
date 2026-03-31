"""Repository scanner – discovers Java and XSLT source files in Maven projects.

Accepts the *root directory* of a single-module or multi-module Maven project.
Recursively walks the entire directory tree to collect all .java, .xsl, and
.xslt files; pom.xml files are parsed to extract Maven coordinates and the
list of declared sub-modules.

A typical multi-module project layout::

    my-project/
    ├── pom.xml                          ← parent POM (declares sub-modules)
    ├── xslt-module/
    │   ├── pom.xml
    │   └── src/main/resources/xslt/
    │       └── mapTrade.xslt
    ├── service-module/
    │   ├── pom.xml
    │   └── src/main/java/com/corp/svc/
    │       └── TradeService.java
    └── model-module/
        ├── pom.xml
        └── src/main/java/com/corp/model/
            └── Trade.java

Pass ``my-project/`` as a single element in ``lib_repos`` or
``project_repos``; the scanner discovers everything underneath it.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from trace_core.logging.logger_factory import LoggerFactory
from trace_core.utils.file_utils import find_files_by_extension
from trace_core.scanner.maven_scanner import MavenScanner

logger = LoggerFactory.get("scanner")


@dataclass
class RepoInfo:
    """Metadata and file lists for one scanned repository root.

    Attributes
    ----------
    name            : Human-readable name — Maven ``artifactId`` when available,
                      otherwise the directory basename.
    root_path       : Absolute path to the repository root directory.
    java_files      : All ``*.java`` files found anywhere under root_path.
    xslt_files      : All ``*.xsl`` / ``*.xslt`` files found under root_path.
    pom_files       : All ``pom.xml`` files found under root_path.
    maven_artifact_id : ``artifactId`` from the root ``pom.xml`` (or None).
    maven_group_id    : ``groupId`` from the root ``pom.xml`` (or None).
    maven_version     : ``version`` from the root ``pom.xml`` (or None).
    maven_modules     : Sub-module directory names declared in ``<modules>``
                        of the root ``pom.xml``.
    file_module_map   : ``{file_path: sub_module_name}`` — maps each source
                        file to the Maven sub-module it belongs to.
    """
    name: str
    root_path: str
    java_files: List[str] = field(default_factory=list)
    xslt_files: List[str] = field(default_factory=list)
    pom_files: List[str] = field(default_factory=list)
    maven_artifact_id: Optional[str] = None
    maven_group_id: Optional[str] = None
    maven_version: Optional[str] = None
    maven_modules: List[str] = field(default_factory=list)
    file_module_map: Dict[str, str] = field(default_factory=dict)

    @property
    def total_files(self) -> int:
        return len(self.java_files) + len(self.xslt_files)

    @property
    def is_multi_module(self) -> bool:
        return len(self.maven_modules) > 0

    @property
    def coordinates(self) -> str:
        return f"{self.maven_group_id}:{self.maven_artifact_id}:{self.maven_version}"


class RepoScanner:
    """Scans repository root directories and returns structured RepoInfo.

    Each entry in ``lib_repos`` or ``project_repos`` must be the **root
    directory** of a Maven project (single-module or multi-module).  The
    scanner recursively discovers every Java and XSLT source file within it
    regardless of how deeply the modules are nested.
    """

    def __init__(self):
        self._maven_scanner = MavenScanner()

    def scan(self, repo_paths: List[str]) -> List[RepoInfo]:
        """Scan all provided repository roots and return a RepoInfo per root.

        Parameters
        ----------
        repo_paths : List[str]
            Root directories of Maven projects.  Each path may be a
            single-module project or the parent directory of a multi-module
            project.  All sub-modules are discovered automatically via the
            parent ``pom.xml``.
        """
        results: List[RepoInfo] = []
        for path in repo_paths:
            abs_path = os.path.abspath(path)
            if not os.path.isdir(abs_path):
                logger.warning(
                    f"Repository path does not exist: {abs_path}",
                    extra={"repository": abs_path},
                )
                continue
            logger.info(f"Scanning repository: {abs_path}", extra={"repository": abs_path})
            info = self._scan_one(abs_path)
            logger.info(
                f"Scan complete: {info.name!r} | "
                f"{'multi-module' if info.is_multi_module else 'single-module'} | "
                f"{len(info.maven_modules)} sub-modules | "
                f"{len(info.java_files)} Java files | "
                f"{len(info.xslt_files)} XSLT files",
                extra={"repository": abs_path},
            )
            results.append(info)
        return results

    # ── internal ──────────────────────────────────────────────────────────────

    def _scan_one(self, abs_path: str) -> RepoInfo:
        """Scan a single repository root directory."""
        # ── Parse root pom.xml for Maven coordinates + sub-module list ────────
        root_pom = os.path.join(abs_path, "pom.xml")
        artifact_id = maven_group_id = maven_version = None
        maven_modules: List[str] = []

        if os.path.isfile(root_pom):
            pom = self._maven_scanner.scan_pom(root_pom)
            if pom:
                artifact_id   = pom.artifact_id
                maven_group_id = pom.group_id
                maven_version  = pom.version
                maven_modules  = pom.modules  # declared <module> children

        # Use Maven artifactId as the canonical repo name when available
        name = artifact_id or os.path.basename(abs_path)

        # ── Collect all pom.xml files ─────────────────────────────────────────
        pom_files: List[str] = []
        for dirpath, _, filenames in os.walk(abs_path):
            for f in filenames:
                if f == "pom.xml":
                    pom_files.append(os.path.join(dirpath, f))

        # ── Discover all Java and XSLT source files ───────────────────────────
        java_files = find_files_by_extension(abs_path, [".java"])
        xslt_files = find_files_by_extension(abs_path, [".xsl", ".xslt"])

        # ── Map each file to its Maven sub-module (if multi-module project) ───
        file_module_map = self._build_file_module_map(
            abs_path, java_files + xslt_files, maven_modules
        )

        return RepoInfo(
            name=name,
            root_path=abs_path,
            java_files=java_files,
            xslt_files=xslt_files,
            pom_files=pom_files,
            maven_artifact_id=artifact_id,
            maven_group_id=maven_group_id,
            maven_version=maven_version,
            maven_modules=maven_modules,
            file_module_map=file_module_map,
        )

    def _build_file_module_map(
        self,
        root: str,
        files: List[str],
        modules: List[str],
    ) -> Dict[str, str]:
        """Return ``{file_path: sub_module_name}`` for every discovered file.

        For a single-module project (no declared ``<modules>``), all files map
        to an empty string (the root is the module).

        For a multi-module project, each file is attributed to the sub-module
        whose directory is the longest prefix of the file path, e.g.:
            ``service-module/src/main/java/...`` → ``"service-module"``
        """
        if not modules:
            return {}

        mapping: Dict[str, str] = {}
        for file_path in files:
            rel = os.path.relpath(file_path, root)
            # The first path component is the sub-module directory name
            top = rel.split(os.sep)[0]
            if top in modules:
                mapping[file_path] = top
        return mapping
