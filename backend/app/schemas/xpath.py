from __future__ import annotations

from pydantic import BaseModel

from .field import XPathEntry


class XPathLookupRequest(BaseModel):
    field_name: str
    jurisdiction_id: str | None = None


class XPathLookupResponse(BaseModel):
    field_name: str
    matches: list[XPathEntry]
    total: int
