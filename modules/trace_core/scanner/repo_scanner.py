"""Repository scanner – discovers Java and XSLT source files."""
import os
from dataclasses import dataclass, field
from typing import List, Optional
from modules.trace_core.logging.logger_factory import LoggerFactory
from modules.trace_core.utils.file_utils import find_files_by_extension

logger = LoggerFactory.get("scanner")


@dataclass
class RepoInfo:
    name: str
    root_path: str
    java_files: List[str] = field(default_factory=list)
    xslt_files: List[str] = field(default_factory=list)
    pom_files: List[str] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.java_files) + len(self.xslt_files)


class RepoScanner:
    """Scans one or more repository roots to discover source files."""

    def scan(self, repo_paths: List[str]) -> List[RepoInfo]:
        """Scan all provided repository paths and return RepoInfo for each."""
        results: List[RepoInfo] = []
        for path in repo_paths:
            if not os.path.isdir(path):
                logger.warning(f"Repository path does not exist: {path}", extra={"repository": path})
                continue
            logger.info(f"Scanning repository: {path}", extra={"repository": path})
            info = self._scan_one(path)
            logger.info(
                f"Scan complete: {len(info.java_files)} Java files, {len(info.xslt_files)} XSLT files",
                extra={"repository": path},
            )
            results.append(info)
        return results

    def _scan_one(self, path: str) -> RepoInfo:
        name = os.path.basename(os.path.abspath(path))
        java_files = find_files_by_extension(path, [".java"])
        xslt_files = find_files_by_extension(path, [".xsl", ".xslt"])
        pom_files = []
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                if f == "pom.xml":
                    pom_files.append(os.path.join(dirpath, f))
        return RepoInfo(name=name, root_path=path, java_files=java_files, xslt_files=xslt_files, pom_files=pom_files)
