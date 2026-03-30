"""Package pattern matching utilities."""
import fnmatch
from typing import List


def matches_pattern(package: str, pattern: str) -> bool:
    """Check if a package name matches a glob-style pattern.

    Supports patterns like ``*nomura*``, ``com.nomura.*``, ``*no*``,
    and exact names.
    """
    if not package or not pattern:
        return False
    # Direct fnmatch for glob patterns
    if fnmatch.fnmatch(package, pattern):
        return True
    # Also try matching any prefix component
    parts = package.split(".")
    for i in range(len(parts)):
        partial = ".".join(parts[:i + 1])
        if fnmatch.fnmatch(partial, pattern):
            return True
    return False


def matches_any_pattern(package: str, patterns: List[str]) -> bool:
    """Return True if the package matches any pattern in the list."""
    return any(matches_pattern(package, p) for p in patterns)
