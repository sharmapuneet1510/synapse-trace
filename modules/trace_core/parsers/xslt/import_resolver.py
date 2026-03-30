"""Resolves xsl:import and xsl:include hrefs to absolute paths."""
import os
from typing import Optional
from modules.trace_core.utils.file_utils import resolve_relative_path


class ImportResolver:
    """Resolves XSLT import/include hrefs relative to a base file."""

    def resolve(self, import_href: str, base_path: str) -> Optional[str]:
        """Return the absolute path of the imported/included file, or None."""
        return resolve_relative_path(base_path, import_href)
