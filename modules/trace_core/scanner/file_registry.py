"""File registry – central index of all discovered source files."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class FileEntry:
    path: str
    file_type: str  # java | xslt
    repository: Optional[str] = None
    module: Optional[str] = None

    @property
    def basename(self) -> str:
        return os.path.basename(self.path)

    @property
    def simple_name(self) -> str:
        return os.path.splitext(self.basename)[0]


class FileRegistry:
    """Maintains an index of all files, queryable by type, name, repo, or module."""

    def __init__(self):
        self._entries: List[FileEntry] = []
        self._by_type: Dict[str, List[FileEntry]] = {"java": [], "xslt": []}
        self._by_name: Dict[str, List[FileEntry]] = {}

    def register_file(self, path: str, file_type: str, repository: Optional[str] = None, module: Optional[str] = None):
        entry = FileEntry(path=path, file_type=file_type, repository=repository, module=module)
        self._entries.append(entry)
        self._by_type.setdefault(file_type, []).append(entry)
        key = entry.simple_name.lower()
        self._by_name.setdefault(key, []).append(entry)

    def get_java_files(self, repository: Optional[str] = None) -> List[str]:
        entries = self._by_type.get("java", [])
        if repository:
            entries = [e for e in entries if e.repository == repository]
        return [e.path for e in entries]

    def get_xslt_files(self, repository: Optional[str] = None) -> List[str]:
        entries = self._by_type.get("xslt", [])
        if repository:
            entries = [e for e in entries if e.repository == repository]
        return [e.path for e in entries]

    def find_by_name(self, name: str) -> List[FileEntry]:
        return self._by_name.get(name.lower(), [])

    def all_entries(self) -> List[FileEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
