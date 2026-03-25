from __future__ import annotations

from pydantic import BaseModel


class TranslationRequest(BaseModel):
    field_name: str
    jurisdiction_id: str
    code_snippet: str | None = None
    xpaths: list[str] | None = None
    dependencies: list[str] | None = None


class TranslationResult(BaseModel):
    field_name: str
    business_derivation: str
    reporting_logic: str
    internal_enrichment: str
    downstream_mapping: str
    examples: list[str]
    operational_guidance: str
