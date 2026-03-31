"""Lineage tracing endpoints.

POST /api/lineage/scan          — run a full field trace via data_lineage.scanner
POST /api/lineage/derive        — run a named LLM prompt against the trace
GET  /api/lineage/export/{field}/{fmt} — export cached trace as html / md / json / neo4j
GET  /api/lineage/prompts       — list registered prompt names
"""
from __future__ import annotations

import asyncio
import logging
import time
from functools import lru_cache
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from ..schemas.lineage import (
    BranchSchema,
    DeriveRequest,
    DeriveResponse,
    EvidenceSchema,
    PromptListResponse,
    ScanRequest,
    ScanResponse,
    SummarySchema,
    TraceEdgeSchema,
    TraceNodeSchema,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lineage", tags=["lineage"])


# ── In-process result cache (field_name → ScanResponse) ──────────────────────
# Replace with Redis / DB-backed cache for multi-process deployments.
_result_cache: Dict[str, object] = {}  # field_name → TraceResult


def _get_scanner():
    """Lazy-import scanner to avoid heavy index load at module import time."""
    import sys, os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    job_dir = os.path.join(root, "backend", "job")
    for _p in (job_dir, root):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from backend.job.data_lineage import scanner
    return scanner


def _get_prompt_registry():
    from backend.app.prompts import prompt_registry
    return prompt_registry


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _serialise_result(result) -> ScanResponse:
    """Convert a TraceResult into a ScanResponse."""
    s = result.summary

    nodes = []
    for n in result.nodes:
        ev = n.evidence
        nodes.append(TraceNodeSchema(
            node_id=n.node_id,
            label=n.label,
            node_type=n.node_type,
            transformation_type=n.transformation_type.value if n.transformation_type else None,
            evidence=EvidenceSchema(
                file_path=ev.file_path,
                class_or_template=ev.class_or_template,
                method_or_template_name=ev.method_or_template_name,
                line_number=ev.line_number,
                condition_text=ev.condition_text,
                raw_code=ev.raw_code,
                repository=ev.repository,
                module=ev.module,
                package=ev.package,
            ),
            conditions=n.metadata.get("conditions", []),
        ))

    edges = [
        TraceEdgeSchema(
            source_id=e.source_id,
            target_id=e.target_id,
            relation=e.relation.value,
            label=e.label,
        )
        for e in result.edges
    ]

    branches = [
        BranchSchema(
            branch_id=b.branch_id,
            condition=b.condition,
            outcome=b.outcome,
            node_ids=b.node_ids,
        )
        for b in result.branches
    ]

    return ScanResponse(
        trace_id=result.trace_id,
        field_name=result.field_name,
        summary=SummarySchema(
            field_name=s.field_name,
            origin=s.origin.value,
            total_nodes=s.total_nodes,
            branch_count=s.branch_count,
            has_xslt=s.has_xslt,
            has_java=s.has_java,
            pipeline_steps=s.pipeline_steps,
            business_explanation=s.business_explanation,
            technical_explanation=s.technical_explanation,
        ),
        nodes=nodes,
        edges=edges,
        branches=branches,
        pipeline_json=result.to_pipeline_json(),
        branch_json=result.to_branch_json(),
        graph_json=result.to_json().get("graph_json", {}),
        metadata=result.metadata,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/scan", response_model=ScanResponse, summary="Trace a field through XSLT + Java")
def scan_field(req: ScanRequest) -> ScanResponse:
    """
    Run a full data lineage trace for a single output field.

    Scans the provided repositories (lib + project), detects XSLT and Java
    origins, follows the call chain, extracts branch conditions, and returns
    a structured trace result.

    The result is cached in-process by field name for use by /derive and /export.
    """
    t0 = time.perf_counter()
    logger.info(
        "POST /lineage/scan: field='%s' project_repos=%s packages=%s",
        req.field_name, req.project_repos, req.deep_scan_packages,
    )

    try:
        sc = _get_scanner()
        project = sc.load_project(
            lib_repos=req.lib_repos,
            project_repos=req.project_repos,
            deep_scan_packages=req.deep_scan_packages,
        )
        trace = project.scan(
            field=req.field_name,
            deep_scan_packages=req.deep_scan_packages,
            extraction=req.extraction,
            transformation=req.transformation,
            max_depth=req.max_depth,
            enable_condition_tracing=req.enable_condition_tracing,
            enable_xslt_imports=req.enable_xslt_imports,
        )
    except Exception as exc:
        logger.exception("scan_field failed for '%s': %s", req.field_name, exc)
        raise HTTPException(status_code=500, detail=str(exc))

    result = trace.result
    _result_cache[req.field_name] = result

    resp = _serialise_result(result)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(
        "POST /lineage/scan: field='%s' → %d nodes, %d branches in %dms",
        req.field_name, len(result.nodes), len(result.branches), elapsed_ms,
    )
    return resp


@router.post("/derive", response_model=DeriveResponse, summary="Run LLM prompt on trace")
async def derive_field(req: DeriveRequest) -> DeriveResponse:
    """
    Run a named LLM prompt against the trace for a given field.

    If the field has already been scanned (cached), the cached result is used.
    Otherwise a fresh scan is run first.

    Available prompt names: business_derivation, technical_summary, field_impact
    (see GET /api/lineage/prompts).
    """
    t0 = time.perf_counter()
    logger.info(
        "POST /lineage/derive: field='%s' prompt='%s'",
        req.field_name, req.prompt_name,
    )

    # Use cached result if available; otherwise scan first
    result = _result_cache.get(req.field_name)
    if result is None:
        logger.info("derive_field: no cached result for '%s', running scan", req.field_name)
        try:
            sc = _get_scanner()
            project = sc.load_project(
                lib_repos=req.lib_repos,
                project_repos=req.project_repos,
                deep_scan_packages=req.deep_scan_packages,
            )
            trace = project.scan(
                field=req.field_name,
                deep_scan_packages=req.deep_scan_packages,
            )
            result = trace.result
            _result_cache[req.field_name] = result
        except Exception as exc:
            logger.exception("derive_field scan failed for '%s': %s", req.field_name, exc)
            raise HTTPException(status_code=500, detail=str(exc))

    # Render prompt — custom_prompt takes priority over prompt_name
    registry = _get_prompt_registry()
    try:
        if req.custom_prompt:
            logger.info(
                "derive_field: using custom_prompt for '%s' (len=%d)",
                req.field_name, len(req.custom_prompt),
            )
            prompt = registry.render_custom(req.custom_prompt, result)
        else:
            if req.prompt_name not in registry:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown prompt '{req.prompt_name}'. "
                           f"Available: {registry.list_prompts()}",
                )
            prompt = registry.render(req.prompt_name, result)

        from backend.app.services.llm_service import llm_service
        context = {"field_name": req.field_name, "trace_id": result.trace_id}
        derivation = await llm_service._call_llm(prompt, context=context)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("derive_field LLM call failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(
        "POST /lineage/derive: field='%s' prompt='%s' derivation_len=%d in %dms",
        req.field_name, req.prompt_name, len(derivation), elapsed_ms,
    )

    return DeriveResponse(
        trace_id=result.trace_id,
        field_name=req.field_name,
        prompt_name=req.prompt_name,
        derivation=derivation,
        model="stub",
    )


@router.get(
    "/export/{field_name}/{fmt}",
    summary="Export trace as HTML, MD, JSON or Neo4j",
)
def export_trace(field_name: str, fmt: str):
    """
    Export a previously-scanned field trace.

    `fmt` must be one of: html, md, json, neo4j

    Requires the field to have been scanned first via POST /api/lineage/scan.
    """
    result = _result_cache.get(field_name)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not in cache. Run POST /api/lineage/scan first.",
        )

    fmt = fmt.lower()

    if fmt == "html":
        from trace_core.exporters.html_exporter import HtmlExporter
        html = HtmlExporter().export(result.summary, result.nodes, result.branches)
        return HTMLResponse(content=html)

    elif fmt == "md":
        from backend.job.data_lineage import _MdExporter
        md = _MdExporter().export(result)
        return PlainTextResponse(content=md, media_type="text/markdown")

    elif fmt == "json":
        return result.to_json()

    elif fmt == "neo4j":
        return result.to_neo4j()

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown format '{fmt}'. Use: html, md, json, neo4j",
        )


@router.get("/prompts", response_model=PromptListResponse, summary="List available LLM prompts")
def list_prompts() -> PromptListResponse:
    """Return the names of all registered LLM prompt templates."""
    registry = _get_prompt_registry()
    return PromptListResponse(prompts=registry.list_prompts())


@router.get("/cache", summary="List cached field names")
def list_cache():
    """Return a list of field names currently held in the in-process result cache."""
    return {"cached_fields": list(_result_cache.keys()), "count": len(_result_cache)}


@router.delete("/cache/{field_name}", summary="Evict a field from the cache")
def evict_cache(field_name: str):
    """Remove a field's cached trace result, forcing a fresh scan next time."""
    if field_name not in _result_cache:
        raise HTTPException(status_code=404, detail=f"'{field_name}' not in cache")
    del _result_cache[field_name]
    logger.info("Cache evicted for field '%s'", field_name)
    return {"evicted": field_name}
