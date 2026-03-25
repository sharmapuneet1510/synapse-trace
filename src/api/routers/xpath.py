from __future__ import annotations

from fastapi import APIRouter

from ..schemas.xpath import XPathLookupRequest, XPathLookupResponse
from ..services.cache import parse_cache

router = APIRouter(prefix="/api/xpath", tags=["xpath"])


@router.post("/lookup", response_model=XPathLookupResponse)
def xpath_lookup(req: XPathLookupRequest):
    matches = []

    if req.jurisdiction_id:
        # Search in a specific jurisdiction
        cache = parse_cache.get(req.jurisdiction_id)
        if cache and cache.xpath_index:
            matches = cache.xpath_index.lookup(req.field_name)
    else:
        # Search across all jurisdictions
        for jid in parse_cache.all_ids():
            cache = parse_cache.get(jid)
            if cache and cache.xpath_index:
                matches.extend(cache.xpath_index.lookup(req.field_name))

    return XPathLookupResponse(
        field_name=req.field_name,
        matches=matches,
        total=len(matches),
    )
