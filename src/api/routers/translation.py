from __future__ import annotations

import logging

from fastapi import APIRouter

from ..schemas.translation import TranslationRequest, TranslationResult
from ..services.translation_service import translation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/translation", tags=["translation"])


@router.post("/explain", response_model=TranslationResult)
def explain_field(req: TranslationRequest):
    logger.info(
        "POST /translation/explain: field='%s' jid='%s'",
        req.field_name, req.jurisdiction_id,
    )
    return translation_service.explain(
        field_name=req.field_name,
        jurisdiction_id=req.jurisdiction_id,
        code_snippet=req.code_snippet,
        xpaths=req.xpaths,
        dependencies=req.dependencies,
    )
