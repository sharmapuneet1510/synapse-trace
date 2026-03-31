"""File system utility helpers."""
import os
from typing import List, Optional


def find_files_by_extension(root: str, extensions: List[str]) -> List[str]:
    """Recursively find all files with the given extensions under root."""
    results = []
    ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if os.path.splitext(fname)[1].lower() in ext_set:
                results.append(os.path.join(dirpath, fname))
    return sorted(results)


def read_file_safe(path: str, encoding: str = "utf-8") -> Optional[str]:
    """Read a file safely, returning None on any error."""
    try:
        with open(path, "r", encoding=encoding, errors="replace") as fh:
            return fh.read()
    except Exception:
        return None


def resolve_relative_path(base_path: str, relative_href: str) -> Optional[str]:
    """Resolve a relative path (e.g. from xsl:import href) against a base file path."""
    try:
        base_dir = os.path.dirname(os.path.abspath(base_path))
        resolved = os.path.normpath(os.path.join(base_dir, relative_href))
        return resolved if os.path.exists(resolved) else None
    except Exception:
        return None
