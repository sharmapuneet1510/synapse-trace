"""Field detail assembly from cached lineage data."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def _build_match_keys(field_name: str) -> set:  # noqa: E402
    """Generate normalized match keys for fuzzy field-name matching."""
    if not field_name:
        return set()
    name = field_name.upper().strip()
    keys = {name}
    for prefix in ("N_", "B_", "S_", "I_", "D_"):
        if name.startswith(prefix):
            keys.add(name[len(prefix):])
    keys.add(name.replace("_", ""))
    return {k for k in keys if k}

from ..schemas.field import DependencyRef, FieldDetail, JavaReference, XPathEntry  # noqa: E402
from .cache import parse_cache  # noqa: E402
from . import jurisdiction_service  # noqa: E402


def get_field_detail(jurisdiction_id: str, field_name: str) -> FieldDetail | None:
    """Build a complete field detail view from cached parse results."""
    logger.debug("get_field_detail: '%s' in '%s'", field_name, jurisdiction_id)
    field_config, config_type = jurisdiction_service.get_field(
        jurisdiction_id, field_name
    )
    if not field_config:
        logger.info(
            "get_field_detail: field '%s' not found in jurisdiction '%s'",
            field_name, jurisdiction_id,
        )
        return None

    cache = parse_cache.get(jurisdiction_id)
    if not cache:
        logger.debug(
            "get_field_detail: no cache for jurisdiction '%s' — returning static config only",
            jurisdiction_id,
        )
    elif cache.status != "ready":
        logger.debug(
            "get_field_detail: cache for '%s' has status '%s' — returning static config only",
            jurisdiction_id, cache.status,
        )

    detail = FieldDetail(
        jurisdiction_id=jurisdiction_id,
        field_name=field_config.field_name,
        header=field_config.header,
        asset_classes=field_config.asset_classes,
        config_type=config_type or "",
    )

    if not cache or cache.status != "ready":
        return detail

    # Match keys for this field
    match_keys = _build_match_keys(field_name)

    # Find XSLT findings referencing this field
    xslt_logic_snippet = None
    xslt_file = None
    xslt_line = None
    input_xpaths: list[XPathEntry] = []

    for finding in cache.xslt_findings:
        source_keys = set()
        if finding.field_source:
            source_keys = _build_match_keys(finding.field_source)
        target_keys = set()
        if finding.field_target:
            target_keys = _build_match_keys(finding.field_target)

        if match_keys & (source_keys | target_keys):
            # First match gives us the XSLT logic snippet
            if not xslt_logic_snippet and finding.meta:
                xslt_logic_snippet = finding.meta.code_snippet
                xslt_file = str(finding.meta.file_path) if finding.meta.file_path else None
                xslt_line = finding.meta.line_number

            # Build XPath entries
            if finding.field_source:
                input_xpaths.append(
                    XPathEntry(
                        name=finding.field_source.split("/")[-1] if "/" in finding.field_source else finding.field_source,
                        source=str(finding.meta.file_path).split("/")[-1] if finding.meta and finding.meta.file_path else "",
                        xpath=finding.field_source,
                        template=finding.template_name,
                        output_element=finding.field_target,
                        line=finding.meta.line_number if finding.meta else None,
                    )
                )

    detail.xslt_logic = xslt_logic_snippet
    detail.xslt_file = xslt_file
    detail.xslt_line = xslt_line

    # XPath reverse lookup
    if cache.xpath_index:
        xpath_results = cache.xpath_index.lookup(field_name)
        # Merge, dedup by xpath+source
        seen = {(x.xpath, x.source) for x in input_xpaths}
        for xr in xpath_results:
            key = (xr.xpath, xr.source)
            if key not in seen:
                seen.add(key)
                input_xpaths.append(xr)

    detail.input_xpaths = input_xpaths

    # Find dependencies from lineage edges
    dependencies: list[DependencyRef] = []
    if cache.lineage:
        # Build node lookup
        node_map = {n.id: n for n in cache.lineage.nodes}
        # Find nodes matching this field
        field_node_ids = set()
        for node in cache.lineage.nodes:
            node_keys = _build_match_keys(node.label)
            if match_keys & node_keys:
                field_node_ids.add(node.id)

        # Find edges connected to these nodes
        for edge in cache.lineage.edges:
            if edge.source_id in field_node_ids or edge.target_id in field_node_ids:
                other_id = (
                    edge.target_id
                    if edge.source_id in field_node_ids
                    else edge.source_id
                )
                other_node = node_map.get(other_id)
                if other_node:
                    dep_type = "java" if "java" in other_node.id else "xslt"
                    dependencies.append(
                        DependencyRef(
                            field_name=other_node.label,
                            relationship=edge.edge_type.value
                            if hasattr(edge.edge_type, "value")
                            else str(edge.edge_type),
                            source_type=dep_type,
                            file_path=other_node.meta.file_path
                            if other_node.meta
                            else None,
                            line_number=other_node.meta.line_number
                            if other_node.meta
                            else None,
                        )
                    )

    logger.debug(
        "get_field_detail: '%s' resolved — %d XPaths, %d dependencies",
        field_name, len(input_xpaths), len(dependencies),
    )
    detail.dependencies = dependencies

    # Find Java references
    java_refs: list[JavaReference] = []
    for finding in cache.java_findings:
        finding_keys = set()
        if finding.field_name:
            finding_keys |= _build_match_keys(finding.field_name)
        if finding.target_field:
            finding_keys |= _build_match_keys(finding.target_field)

        if match_keys & finding_keys:
            java_refs.append(
                JavaReference(
                    class_name=finding.class_name,
                    method_name=finding.method_name,
                    finding_type=finding.finding_type,
                    code_snippet=finding.meta.code_snippet if finding.meta else None,
                    file_path=str(finding.meta.file_path)
                    if finding.meta and finding.meta.file_path
                    else None,
                    line_number=finding.meta.line_number if finding.meta else None,
                )
            )

    detail.java_references = java_refs
    logger.debug(
        "get_field_detail: '%s' complete — %d Java refs, xslt_file=%s",
        field_name, len(java_refs), detail.xslt_file,
    )
    return detail
