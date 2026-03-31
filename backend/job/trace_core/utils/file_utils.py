"""File system utility helpers."""
import os
from typing import List, Optional

# ── Directories always skipped regardless of depth ────────────────────────────
_SKIP_DIRS = frozenset({
    # Build artefacts
    "target", "build", "out", "dist", "bin", "obj",
    # VCS / IDE metadata
    ".git", ".svn", ".hg", ".idea", ".vscode",
    # JS / Python package caches
    "node_modules", "__pycache__",
})

# ── Path segments that mark test/generated subtrees ──────────────────────────
# A directory is skipped if its path (relative to the walk root) contains one
# of these segment sequences joined by the OS path separator.  This catches:
#   src/test/java, src/test/resources          (standard Maven)
#   src/main/test                              (non-standard variant)
#   src/it (integration tests), src/itest
#   generated-sources, generated-test-sources  (annotation processors)
_SKIP_PATH_SEGMENTS = (
    os.path.join("src", "test"),
    os.path.join("src", "main", "test"),
    os.path.join("src", "it"),
    os.path.join("src", "itest"),
    "generated-sources",
    "generated-test-sources",
)


def _is_test_path(dirpath: str, root: str) -> bool:
    """Return True if *dirpath* falls inside a test or generated-source tree."""
    # Use the relative path so we don't accidentally match the root itself
    rel = os.path.relpath(dirpath, root)
    # Normalise to forward slashes for a consistent contains-check on all OS
    rel_fwd = rel.replace(os.sep, "/")
    return any(seg.replace(os.sep, "/") in rel_fwd for seg in _SKIP_PATH_SEGMENTS)


def find_files_by_extension(root: str, extensions: List[str]) -> List[str]:
    """Recursively find all *production* source files with the given extensions.

    Skips:
    - Build-output directories  (target/, build/, dist/, …)
    - VCS / IDE metadata        (.git/, .idea/, …)
    - Test source trees         (src/test/, src/main/test/, src/it/, …)
    - Generated-source trees    (generated-sources/, generated-test-sources/)
    - Any path that is not a regular file (directories with an extension)
    """
    results = []
    abs_root = os.path.abspath(root)
    ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}

    for dirpath, dirnames, filenames in os.walk(abs_root):
        # 1. Prune well-known non-source dirs in-place
        dirnames[:] = [
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith(".")
        ]

        # 2. Skip the entire subtree if this dirpath is inside a test/generated tree
        if _is_test_path(dirpath, abs_root):
            dirnames.clear()   # stop os.walk from descending further
            continue

        for fname in filenames:
            if os.path.splitext(fname)[1].lower() in ext_set:
                full = os.path.join(dirpath, fname)
                if os.path.isfile(full):
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
