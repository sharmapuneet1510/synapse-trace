"""File system utility helpers."""
import os
from typing import List, Optional


_SKIP_DIRS = frozenset({
    "target", "build", "out", ".git", ".svn", ".hg",
    "node_modules", ".idea", ".vscode", "__pycache__",
})


def find_files_by_extension(root: str, extensions: List[str]) -> List[str]:
    """Recursively find all *files* with the given extensions under root.

    Skips common build-output and hidden directories (target/, build/,
    .git/, node_modules/, etc.) and silently ignores any path that turns
    out to be a directory rather than a regular file.
    """
    results = []
    ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune non-source directories in-place so os.walk skips them entirely
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if os.path.splitext(fname)[1].lower() in ext_set:
                full = os.path.join(dirpath, fname)
                if os.path.isfile(full):   # exclude any directory that has an extension
                    results.append(full)
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
