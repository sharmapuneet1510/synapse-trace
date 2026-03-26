from __future__ import annotations

import logging

from fastapi import APIRouter

from ..schemas.xpath import XPathLookupRequest, XPathLookupResponse
from ..services.cache import parse_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/xpath", tags=["xpath"])


@router.post("/lookup", response_model=XPathLookupResponse)
def xpath_lookup(req: XPathLookupRequest):
    scope = req.jurisdiction_id or "all jurisdictions"
    logger.debug("POST /xpath/lookup: field='%s' scope=%s", req.field_name, scope)
    matches = []

    if req.jurisdiction_id:
        cache = parse_cache.get(req.jurisdiction_id)
        if cache and cache.xpath_index:
            matches = cache.xpath_index.lookup(req.field_name)
        elif not cache:
            logger.debug(
                "POST /xpath/lookup: no cache for '%s'", req.jurisdiction_id
            )
    else:
        for jid in parse_cache.all_ids():
            cache = parse_cache.get(jid)
            if cache and cache.xpath_index:
                matches.extend(cache.xpath_index.lookup(req.field_name))

    logger.info(
        "POST /xpath/lookup: '%s' in %s → %d match(es)",
        req.field_name, scope, len(matches),
    )
    return XPathLookupResponse(
        field_name=req.field_name,
        matches=matches,
        total=len(matches),
    )
