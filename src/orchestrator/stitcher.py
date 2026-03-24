"""Stitcher: connects Java and XSLT findings into a unified lineage graph.

Handles field name variations across languages and repositories:
  - XSLT: N_EFFECTIVE_DATE
  - Java:  MessageKey.N_EFFECTIVE_DATE, "N_EFFECTIVE_DATE", effectiveDate
  - Cross-repo: library constants referenced from application code
"""

from __future__ import annotations

import re
from collections import defaultdict

from orchestrator.models import (
    EdgeType,
    JavaFinding,
    LineageEdge,
    LineageNode,
    NodeMeta,
    NodeType,
    StitchedLineage,
    XsltFinding,
)


def _normalize_field(name: str) -> str:
    """Normalize a field name for cross-language matching.

    Strips get/set/is prefix and lowercases the first character.
    """
    name = re.sub(r"^(get|set|is)(?=[A-Z])", "", name)
    return (name[0].lower() + name[1:]) if name else name


def _extract_canonical_key(raw: str) -> str:
    """Extract the bare key from qualified or prefixed references.

    Examples:
        "MessageKey.N_EFFECTIVE_DATE"  -> "N_EFFECTIVE_DATE"
        "FieldNames.COUNTERPARTY_ID"   -> "COUNTERPARTY_ID"
        "N_EFFECTIVE_DATE"             -> "N_EFFECTIVE_DATE"
        "com.bank.Keys.TRADE_AMOUNT"   -> "TRADE_AMOUNT"
    """
    # Strip everything before the last dot (qualifier)
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    return raw.strip()


def _to_snake_upper(name: str) -> str:
    """Convert camelCase/PascalCase to UPPER_SNAKE_CASE.

    Examples:
        "effectiveDate"    -> "EFFECTIVE_DATE"
        "counterpartyName" -> "COUNTERPARTY_NAME"
        "N_EFFECTIVE_DATE" -> "N_EFFECTIVE_DATE"  (already uppercase)
    """
    if name == name.upper():
        return name
    # Insert underscore before uppercase letters preceded by lowercase
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return s.upper()


def _to_camel(name: str) -> str:
    """Convert UPPER_SNAKE_CASE to camelCase.

    Examples:
        "N_EFFECTIVE_DATE"  -> "nEffectiveDate"
        "COUNTERPARTY_NAME" -> "counterpartyName"
        "effectiveDate"     -> "effectiveDate"  (already camel)
    """
    if "_" not in name:
        return (name[0].lower() + name[1:]) if name else name
    parts = name.lower().split("_")
    # Filter out single-letter prefixes like "N" that are just naming convention
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _build_match_keys(raw_name: str) -> set[str]:
    """Build all canonical forms of a field name for fuzzy cross-language matching.

    Given any one variation, produces all forms so that matching is symmetric.
    """
    canonical = _extract_canonical_key(raw_name)
    keys: set[str] = set()

    # The raw canonical
    keys.add(canonical.lower())

    # UPPER_SNAKE form
    snake = _to_snake_upper(canonical)
    keys.add(snake.lower())

    # camelCase form
    camel = _to_camel(canonical)
    keys.add(camel.lower())

    # Normalized (strip get/set/is)
    norm = _normalize_field(canonical)
    keys.add(norm.lower())

    # Also try stripping a single-letter prefix: N_EFFECTIVE_DATE -> EFFECTIVE_DATE
    if re.match(r"^[A-Z]_", canonical):
        stripped = canonical[2:]
        keys.add(stripped.lower())
        keys.add(_to_camel(stripped).lower())

    return keys


class Stitcher:
    """Builds a StitchedLineage graph from Java and XSLT findings across multiple repos."""

    def stitch(
        self,
        java_findings: list[JavaFinding],
        xslt_findings: list[XsltFinding],
    ) -> StitchedLineage:
        nodes: dict[str, LineageNode] = {}
        edges: set[tuple[str, str, EdgeType]] = set()
        edge_list: list[LineageEdge] = []

        def _add_node(node: LineageNode) -> None:
            if node.id not in nodes:
                nodes[node.id] = node

        def _add_edge(src: str, tgt: str, etype: EdgeType, props: dict | None = None) -> None:
            key = (src, tgt, etype)
            if key not in edges and src in nodes and tgt in nodes:
                edges.add(key)
                edge_list.append(LineageEdge(src, tgt, etype, props or {}))

        # ===========================
        # Index Java findings
        # ===========================

        # Multi-key index: every canonical form -> list of findings
        java_field_index: dict[str, list[tuple[str, JavaFinding]]] = defaultdict(list)
        java_classes: set[str] = set()
        java_methods: dict[str, JavaFinding] = {}
        java_unmarshals: list[JavaFinding] = []
        java_xslt_refs: list[JavaFinding] = []
        # Constant definitions: qualifier.CONST -> bare CONST (for cross-repo resolution)
        java_constants: dict[str, list[JavaFinding]] = defaultdict(list)

        for jf in java_findings:
            java_classes.add(jf.class_name)
            repo_tag = f"[{jf.repo_name}]" if jf.repo_name else ""

            if jf.finding_type == "field_mapping" and jf.field_name:
                node_id = f"java::field::{jf.class_name}::{jf.field_name}"
                for key in _build_match_keys(jf.field_name):
                    java_field_index[key].append((node_id, jf))

            elif jf.finding_type == "constant_ref" and jf.field_name:
                bare = _extract_canonical_key(jf.field_name)
                qualified = f"{jf.target_class}.{bare}" if jf.target_class else bare
                node_id = f"java::const::{jf.class_name}::{qualified}"
                for key in _build_match_keys(bare):
                    java_field_index[key].append((node_id, jf))
                java_constants[bare.lower()].append(jf)

            elif jf.finding_type == "string_literal" and jf.field_name:
                bare = _extract_canonical_key(jf.field_name)
                node_id = f"java::literal::{jf.class_name}::{bare}"
                for key in _build_match_keys(bare):
                    java_field_index[key].append((node_id, jf))

            elif jf.finding_type == "unmarshal":
                java_unmarshals.append(jf)

            elif jf.finding_type == "xslt_ref":
                java_xslt_refs.append(jf)

            elif jf.finding_type == "method_call" and jf.method_name:
                key = f"{jf.class_name}::{jf.method_name}"
                java_methods[key] = jf

        # ===========================
        # Index XSLT findings
        # ===========================
        xslt_field_index: dict[str, list[tuple[str, XsltFinding]]] = defaultdict(list)
        xslt_templates: dict[str, XsltFinding] = {}

        for xf in xslt_findings:
            tpl_key = f"xslt::{xf.template_name}"
            if tpl_key not in xslt_templates:
                xslt_templates[tpl_key] = xf

            if xf.finding_type == "value_of" and xf.field_source:
                from orchestrator.parsers.xslt_parser import XsltParser

                field_name = XsltParser._extract_field_name(xf.field_source)
                if field_name:
                    field_id = f"xslt::field::{xf.template_name}::{xf.field_source}"
                    for key in _build_match_keys(field_name):
                        xslt_field_index[key].append((field_id, xf))

        # =====================
        # Phase 1: Create nodes
        # =====================

        # Java class nodes
        for cls in java_classes:
            repo_props = {}
            # Find repo_name from any finding in this class
            for jf in java_findings:
                if jf.class_name == cls and jf.repo_name:
                    repo_props["repo"] = jf.repo_name
                    break
            _add_node(
                LineageNode(
                    id=f"java::class::{cls}",
                    label=cls.rsplit(".", 1)[-1],
                    node_type=NodeType.JAVA_CLASS,
                    meta=NodeMeta(file_path="", line_number=0, code_snippet=cls),
                    properties=repo_props,
                )
            )

        # Java nodes from findings
        for jf in java_findings:
            cls_id = f"java::class::{jf.class_name}"
            repo_props = {"repo": jf.repo_name} if jf.repo_name else {}

            if jf.finding_type == "method_call" and jf.method_name:
                method_id = f"java::method::{jf.class_name}::{jf.method_name}"
                _add_node(
                    LineageNode(
                        id=method_id,
                        label=f"{jf.class_name.rsplit('.', 1)[-1]}.{jf.method_name}()",
                        node_type=NodeType.JAVA_METHOD,
                        meta=jf.meta,
                        properties=repo_props,
                    )
                )
                _add_edge(cls_id, method_id, EdgeType.CALLS)

                if jf.target_class and jf.target_field:
                    target_id = f"java::method::{jf.target_class}::{jf.target_field}"
                    _add_node(
                        LineageNode(
                            id=target_id,
                            label=f"{jf.target_class}.{jf.target_field}()",
                            node_type=NodeType.JAVA_METHOD,
                            meta=jf.meta,
                            properties=repo_props,
                        )
                    )
                    _add_edge(method_id, target_id, EdgeType.CALLS)

            elif jf.finding_type == "unmarshal" and jf.target_class:
                dto_id = f"java::dto::{jf.target_class}"
                method_id = (
                    f"java::method::{jf.class_name}::{jf.method_name}"
                    if jf.method_name
                    else cls_id
                )
                _add_node(
                    LineageNode(
                        id=dto_id,
                        label=f"DTO:{jf.target_class}",
                        node_type=NodeType.DTO,
                        meta=jf.meta,
                        properties=repo_props,
                    )
                )
                if jf.method_name:
                    _add_node(
                        LineageNode(
                            id=method_id,
                            label=f"{jf.class_name.rsplit('.', 1)[-1]}.{jf.method_name}()",
                            node_type=NodeType.JAVA_METHOD,
                            meta=jf.meta,
                            properties=repo_props,
                        )
                    )
                _add_edge(method_id, dto_id, EdgeType.UNMARSHALS_TO)

            elif jf.finding_type == "field_mapping" and jf.field_name and jf.target_field:
                src_field_id = f"java::field::{jf.class_name}::{jf.field_name}"
                tgt_field_id = f"java::field::{jf.target_class}::{jf.target_field}"
                _add_node(
                    LineageNode(
                        id=src_field_id,
                        label=jf.field_name,
                        node_type=NodeType.JAVA_FIELD,
                        meta=jf.meta,
                        properties={"owner": jf.class_name, **repo_props},
                    )
                )
                _add_node(
                    LineageNode(
                        id=tgt_field_id,
                        label=jf.target_field,
                        node_type=NodeType.JAVA_FIELD,
                        meta=jf.meta,
                        properties={"owner": jf.target_class or "", **repo_props},
                    )
                )
                _add_edge(src_field_id, tgt_field_id, EdgeType.DERIVED_FROM)

            elif jf.finding_type == "constant_ref" and jf.field_name:
                bare = _extract_canonical_key(jf.field_name)
                qualified = f"{jf.target_class}.{bare}" if jf.target_class else bare
                const_id = f"java::const::{jf.class_name}::{qualified}"
                _add_node(
                    LineageNode(
                        id=const_id,
                        label=f"{qualified}",
                        node_type=NodeType.JAVA_CONSTANT,
                        meta=jf.meta,
                        properties={"qualifier": jf.target_class or "", "bare_name": bare, **repo_props},
                    )
                )
                # Link constant to the method that uses it
                if jf.method_name:
                    method_id = f"java::method::{jf.class_name}::{jf.method_name}"
                    _add_edge(method_id, const_id, EdgeType.CALLS)

            elif jf.finding_type == "string_literal" and jf.field_name:
                bare = _extract_canonical_key(jf.field_name)
                lit_id = f"java::literal::{jf.class_name}::{bare}"
                _add_node(
                    LineageNode(
                        id=lit_id,
                        label=f'"{bare}"',
                        node_type=NodeType.JAVA_CONSTANT,
                        meta=jf.meta,
                        properties={"literal": True, "bare_name": bare, **repo_props},
                    )
                )
                if jf.method_name:
                    method_id = f"java::method::{jf.class_name}::{jf.method_name}"
                    _add_edge(method_id, lit_id, EdgeType.CALLS)

        # XSLT template nodes
        for tpl_key, xf in xslt_templates.items():
            repo_props = {"repo": xf.repo_name} if xf.repo_name else {}
            _add_node(
                LineageNode(
                    id=tpl_key,
                    label=f"XSLT:{xf.template_name}",
                    node_type=NodeType.XSLT_TEMPLATE,
                    meta=xf.meta,
                    properties={"match": xf.template_match, **repo_props},
                )
            )

        # XSLT field nodes + edges
        for xf in xslt_findings:
            tpl_id = f"xslt::{xf.template_name}"
            repo_props = {"repo": xf.repo_name} if xf.repo_name else {}

            if xf.finding_type == "value_of" and xf.field_source:
                field_id = f"xslt::field::{xf.template_name}::{xf.field_source}"
                target_label = xf.field_target or xf.field_source
                _add_node(
                    LineageNode(
                        id=field_id,
                        label=target_label,
                        node_type=NodeType.XSLT_FIELD,
                        meta=xf.meta,
                        properties={"xpath": xf.field_source, "output_element": xf.field_target, **repo_props},
                    )
                )
                _add_edge(tpl_id, field_id, EdgeType.TRANSFORMS)

            elif xf.finding_type == "template_call" and xf.field_target:
                called_id = f"xslt::{xf.field_target}"
                _add_edge(tpl_id, called_id, EdgeType.CALLS)

        # ==========================================
        # Phase 2: Java → XSLT execution sequence
        # ==========================================

        # Build XSLT file nodes from xslt_findings (group by source file)
        xslt_files_seen: dict[str, str] = {}  # file_path -> node_id
        for xf in xslt_findings:
            fp = xf.meta.file_path
            if fp and fp not in xslt_files_seen:
                from pathlib import Path as _P
                file_stem = _P(fp).stem
                file_id = f"xslt::file::{file_stem}"
                xslt_files_seen[fp] = file_id
                repo_props = {"repo": xf.repo_name} if xf.repo_name else {}
                _add_node(
                    LineageNode(
                        id=file_id,
                        label=f"{_P(fp).name}",
                        node_type=NodeType.XSLT_FILE,
                        meta=NodeMeta(file_path=fp, line_number=0, code_snippet=fp),
                        properties={"xslt_path": fp, **repo_props},
                    )
                )

        # Link XSLT templates to their source file
        for xf in xslt_findings:
            fp = xf.meta.file_path
            if fp in xslt_files_seen:
                tpl_id = f"xslt::{xf.template_name}"
                file_id = xslt_files_seen[fp]
                if tpl_id in nodes:
                    _add_edge(file_id, tpl_id, EdgeType.CALLS, {"relation": "contains"})

        # Java xslt_ref findings → LOADS_XSLT edges
        # Match Java XSLT references to XSLT file nodes by filename
        for jf in java_xslt_refs:
            cls_id = f"java::class::{jf.class_name}"
            method_id = (
                f"java::method::{jf.class_name}::{jf.method_name}"
                if jf.method_name
                else cls_id
            )
            repo_props = {"repo": jf.repo_name} if jf.repo_name else {}

            # Ensure the method node exists
            if jf.method_name:
                _add_node(
                    LineageNode(
                        id=method_id,
                        label=f"{jf.class_name.rsplit('.', 1)[-1]}.{jf.method_name}()",
                        node_type=NodeType.JAVA_METHOD,
                        meta=jf.meta,
                        properties=repo_props,
                    )
                )
                _add_edge(cls_id, method_id, EdgeType.CALLS)

            # Match the xslt filename to a known XSLT file node
            xslt_stem = jf.field_name  # e.g. "trade_transform"
            xslt_full_path = jf.target_field  # e.g. "path/to/trade_transform.xsl"

            matched_file_id = None
            # Try exact stem match
            candidate_id = f"xslt::file::{xslt_stem}"
            if candidate_id in nodes:
                matched_file_id = candidate_id
            else:
                # Try matching by file path suffix
                for fp, fid in xslt_files_seen.items():
                    if fp.endswith(xslt_full_path) or _P(fp).stem == xslt_stem:
                        matched_file_id = fid
                        break

            if matched_file_id:
                _add_edge(
                    method_id,
                    matched_file_id,
                    EdgeType.LOADS_XSLT,
                    {"xslt_path": xslt_full_path, "ref_from": jf.class_name},
                )
            else:
                # Create a placeholder XSLT file node (unresolved)
                placeholder_id = f"xslt::file::{xslt_stem}"
                _add_node(
                    LineageNode(
                        id=placeholder_id,
                        label=f"{xslt_full_path} (unresolved)",
                        node_type=NodeType.XSLT_FILE,
                        meta=jf.meta,
                        properties={"xslt_path": xslt_full_path, "unresolved": True, **repo_props},
                    )
                )
                _add_edge(
                    method_id,
                    placeholder_id,
                    EdgeType.LOADS_XSLT,
                    {"xslt_path": xslt_full_path, "ref_from": jf.class_name},
                )

        # ==========================================
        # Phase 3: Cross-language field stitching
        # ==========================================

        # Match XSLT fields to Java fields/constants/literals by canonical keys
        for match_key, xslt_entries in xslt_field_index.items():
            if match_key in java_field_index:
                for xslt_field_id, xf in xslt_entries:
                    for java_node_id, jf in java_field_index[match_key]:
                        # Determine if cross-repo
                        is_cross_repo = (
                            xf.repo_name and jf.repo_name and xf.repo_name != jf.repo_name
                        )
                        edge_type = EdgeType.CROSS_REPO if is_cross_repo else EdgeType.DERIVED_FROM
                        _add_edge(
                            xslt_field_id,
                            java_node_id,
                            edge_type,
                            {
                                "match_type": "field_name",
                                "match_key": match_key,
                                "xslt_repo": xf.repo_name,
                                "java_repo": jf.repo_name,
                            },
                        )

        # Cross-repo Java-to-Java: constant in repo A used in repo B
        # Group constants by bare name, link across repos
        bare_name_groups: dict[str, list[tuple[str, JavaFinding]]] = defaultdict(list)
        for jf in java_findings:
            if jf.finding_type in ("constant_ref", "string_literal") and jf.field_name:
                bare = _extract_canonical_key(jf.field_name).lower()
                if jf.finding_type == "constant_ref":
                    qualified = f"{jf.target_class}.{_extract_canonical_key(jf.field_name)}" if jf.target_class else _extract_canonical_key(jf.field_name)
                    nid = f"java::const::{jf.class_name}::{qualified}"
                else:
                    nid = f"java::literal::{jf.class_name}::{_extract_canonical_key(jf.field_name)}"
                bare_name_groups[bare].append((nid, jf))

        for bare, group in bare_name_groups.items():
            if len(group) < 2:
                continue
            repos_seen = {jf.repo_name for _, jf in group if jf.repo_name}
            if len(repos_seen) < 2:
                continue
            # Link all cross-repo occurrences
            for idx, (nid_a, jf_a) in enumerate(group):
                for nid_b, jf_b in group[idx + 1 :]:
                    if jf_a.repo_name != jf_b.repo_name:
                        _add_edge(
                            nid_a,
                            nid_b,
                            EdgeType.CROSS_REPO,
                            {
                                "match_type": "cross_repo_constant",
                                "bare_name": bare,
                                "repo_a": jf_a.repo_name,
                                "repo_b": jf_b.repo_name,
                            },
                        )

        # Match XSLT template @match to Java unmarshal DTO class names
        for tpl_key, xf in xslt_templates.items():
            match_str = (xf.template_match or "").lower()
            for jf in java_unmarshals:
                dto_name = (jf.target_class or "").lower()
                if dto_name and dto_name in match_str:
                    dto_id = f"java::dto::{jf.target_class}"
                    is_cross_repo = (
                        xf.repo_name and jf.repo_name and xf.repo_name != jf.repo_name
                    )
                    edge_type = EdgeType.CROSS_REPO if is_cross_repo else EdgeType.TRANSFORMS
                    _add_edge(
                        tpl_key,
                        dto_id,
                        edge_type,
                        {
                            "match_type": "dto_name",
                            "xslt_repo": xf.repo_name,
                            "java_repo": jf.repo_name,
                        },
                    )

        return StitchedLineage(
            nodes=list(nodes.values()),
            edges=edge_list,
        )
