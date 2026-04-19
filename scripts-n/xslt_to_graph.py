#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET

XSL_NS = "http://www.w3.org/1999/XSL/Transform"
VAR_REF_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_.-]*)")


def qname(local: str) -> str:
    return f"{{{XSL_NS}}}{local}"


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def dedupe_keep_order(values: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def extract_var_refs(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return VAR_REF_RE.findall(text)


@dataclass
class TemplateDef:
    name: str
    file: str
    direct_xpaths: List[str] = field(default_factory=list)
    direct_variables: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)


@dataclass
class VariableDef:
    name: str
    file: str
    select: Optional[str] = None
    text: Optional[str] = None
    direct_variables: List[str] = field(default_factory=list)
    direct_xpaths: List[str] = field(default_factory=list)


@dataclass
class ConditionDef:
    id: str
    template_name: str
    file: str
    order: int
    kind: str
    test: Optional[str] = None
    direct_variables: List[str] = field(default_factory=list)
    direct_xpaths: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)


class XsltGraphBuilder:
    def __init__(self) -> None:
        self.loaded_files: Set[Path] = set()
        self.templates: Dict[str, TemplateDef] = {}
        self.variables: Dict[str, VariableDef] = {}
        self.conditions: Dict[str, ConditionDef] = {}
        self.parse_errors: List[str] = []

    def load(self, root_file: Path) -> None:
        self._load_recursive(root_file.resolve())

    def _load_recursive(self, file_path: Path) -> None:
        if file_path in self.loaded_files:
            return
        if not file_path.exists():
            self.parse_errors.append(f"Missing imported file: {file_path}")
            return

        self.loaded_files.add(file_path)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception as exc:
            self.parse_errors.append(f"Failed parsing {file_path}: {exc}")
            return

        for node in root.findall(f"./{qname('import')}") + root.findall(f"./{qname('include')}"):
            href = node.attrib.get("href")
            if href:
                self._load_recursive((file_path.parent / href).resolve())

        for node in root.findall(f"./{qname('variable')}"):
            self._parse_global_variable(node, file_path)

        for node in root.findall(f".//{qname('template')}"):
            name = node.attrib.get("name")
            if name:
                self._parse_template(node, file_path, name)

    def _parse_global_variable(self, node: ET.Element, file_path: Path) -> None:
        name = node.attrib.get("name")
        if not name:
            return
        select = node.attrib.get("select")
        text = "".join(node.itertext()).strip() or None
        refs = dedupe_keep_order(extract_var_refs(select) + extract_var_refs(text))
        xpaths = dedupe_keep_order(self._extract_xpaths_from_value(select) + self._extract_xpaths_from_value(text))
        self.variables[name] = VariableDef(
            name=name,
            file=str(file_path),
            select=select,
            text=text,
            direct_variables=refs,
            direct_xpaths=xpaths,
        )

    def _parse_template(self, node: ET.Element, file_path: Path, name: str) -> None:
        template = TemplateDef(name=name, file=str(file_path))
        condition_counter = 0

        for inner in node.iter():
            tag = strip_ns(inner.tag)
            if tag == "call-template":
                target = inner.attrib.get("name")
                if target:
                    template.calls.append(target)
            elif tag in ("value-of", "sequence", "copy-of"):
                expr = inner.attrib.get("select")
                template.direct_variables.extend(extract_var_refs(expr))
                template.direct_xpaths.extend(self._extract_xpaths_from_value(expr))
            elif tag in ("if", "for-each", "when", "apply-templates"):
                for attr_name in ("test", "select"):
                    expr = inner.attrib.get(attr_name)
                    template.direct_variables.extend(extract_var_refs(expr))
                    template.direct_xpaths.extend(self._extract_xpaths_from_value(expr))
            elif tag == "variable":
                expr = inner.attrib.get("select")
                text = "".join(inner.itertext()).strip() or None
                template.direct_variables.extend(extract_var_refs(expr))
                template.direct_variables.extend(extract_var_refs(text))
                template.direct_xpaths.extend(self._extract_xpaths_from_value(expr))
                template.direct_xpaths.extend(self._extract_xpaths_from_value(text))
            elif tag == "choose":
                for child in list(inner):
                    child_tag = strip_ns(child.tag)
                    if child_tag in ("when", "otherwise"):
                        condition_counter += 1
                        condition = self._parse_condition(
                            child, file_path, name, condition_counter, child_tag
                        )
                        self.conditions[condition.id] = condition
                        template.conditions.append(condition.id)

        template.direct_variables = dedupe_keep_order(template.direct_variables)
        template.direct_xpaths = dedupe_keep_order(template.direct_xpaths)
        template.calls = dedupe_keep_order(template.calls)
        template.conditions = dedupe_keep_order(template.conditions)
        self.templates[name] = template

    def _parse_condition(
        self,
        node: ET.Element,
        file_path: Path,
        template_name: str,
        order: int,
        kind: str,
    ) -> ConditionDef:
        cid = f"{template_name}#{kind}{order}"
        condition = ConditionDef(
            id=cid,
            template_name=template_name,
            file=str(file_path),
            order=order,
            kind=kind,
            test=node.attrib.get("test"),
        )
        if condition.test:
            condition.direct_variables.extend(extract_var_refs(condition.test))
            condition.direct_xpaths.extend(self._extract_xpaths_from_value(condition.test))

        for inner in node.iter():
            tag = strip_ns(inner.tag)
            if inner is node:
                continue
            if tag == "call-template":
                target = inner.attrib.get("name")
                if target:
                    condition.calls.append(target)
            elif tag in ("value-of", "sequence", "copy-of"):
                expr = inner.attrib.get("select")
                condition.direct_variables.extend(extract_var_refs(expr))
                condition.direct_xpaths.extend(self._extract_xpaths_from_value(expr))
            elif tag in ("if", "for-each", "when", "apply-templates"):
                for attr_name in ("test", "select"):
                    expr = inner.attrib.get(attr_name)
                    condition.direct_variables.extend(extract_var_refs(expr))
                    condition.direct_xpaths.extend(self._extract_xpaths_from_value(expr))
            elif tag == "variable":
                expr = inner.attrib.get("select")
                text = "".join(inner.itertext()).strip() or None
                condition.direct_variables.extend(extract_var_refs(expr))
                condition.direct_variables.extend(extract_var_refs(text))
                condition.direct_xpaths.extend(self._extract_xpaths_from_value(expr))
                condition.direct_xpaths.extend(self._extract_xpaths_from_value(text))

        condition.direct_variables = dedupe_keep_order(condition.direct_variables)
        condition.direct_xpaths = dedupe_keep_order(condition.direct_xpaths)
        condition.calls = dedupe_keep_order(condition.calls)
        return condition

    @staticmethod
    def _extract_xpaths_from_value(value: Optional[str]) -> List[str]:
        if not value:
            return []
        text = value.strip()
        if not text:
            return []
        xpath_markers = ("/", "FpML:", "normalize-space(", "exists(", "string(", "lower-case(")
        return [text] if any(marker in text for marker in xpath_markers) else []

    def build_graph(self) -> Dict:
        nodes: Dict[Tuple[str, str], Dict] = {}
        edges: Set[Tuple[str, str, str, str, str]] = set()

        def add_node(kind: str, key: str, props: Dict) -> None:
            nodes[(kind, key)] = {"kind": kind, "key": key, **props}

        def add_edge(from_kind: str, from_key: str, rel: str, to_kind: str, to_key: str) -> None:
            edges.add((from_kind, from_key, rel, to_kind, to_key))

        for file_path in sorted(str(p) for p in self.loaded_files):
            add_node("File", file_path, {"path": file_path, "name": Path(file_path).name})

        for variable in self.variables.values():
            add_node(
                "Variable",
                variable.name,
                {
                    "name": variable.name,
                    "file": variable.file,
                    "select": variable.select,
                    "text": variable.text,
                },
            )
            add_edge("File", variable.file, "DEFINES", "Variable", variable.name)
            for ref in variable.direct_variables:
                add_node("Variable", ref, {"name": ref})
                add_edge("Variable", variable.name, "USES_VARIABLE", "Variable", ref)
            for xpath in variable.direct_xpaths:
                add_node("XPath", xpath, {"expr": xpath})
                add_edge("Variable", variable.name, "USES_XPATH", "XPath", xpath)

        for template in self.templates.values():
            add_node(
                "Template",
                template.name,
                {
                    "name": template.name,
                    "file": template.file,
                },
            )
            add_edge("File", template.file, "DEFINES", "Template", template.name)
            for ref in template.direct_variables:
                add_node("Variable", ref, {"name": ref})
                add_edge("Template", template.name, "USES_VARIABLE", "Variable", ref)
            for xpath in template.direct_xpaths:
                add_node("XPath", xpath, {"expr": xpath})
                add_edge("Template", template.name, "USES_XPATH", "XPath", xpath)
            for target in template.calls:
                add_node("Template", target, {"name": target})
                add_edge("Template", template.name, "CALLS_TEMPLATE", "Template", target)
            for cid in template.conditions:
                condition = self.conditions[cid]
                add_node(
                    "Condition",
                    cid,
                    {
                        "id": cid,
                        "template_name": condition.template_name,
                        "file": condition.file,
                        "order": condition.order,
                        "condition_kind": condition.kind,
                        "test": condition.test,
                    },
                )
                add_edge("Template", template.name, "HAS_CONDITION", "Condition", cid)

        for condition in self.conditions.values():
            for ref in condition.direct_variables:
                add_node("Variable", ref, {"name": ref})
                add_edge("Condition", condition.id, "USES_VARIABLE", "Variable", ref)
            for xpath in condition.direct_xpaths:
                add_node("XPath", xpath, {"expr": xpath})
                add_edge("Condition", condition.id, "SELECTS_XPATH", "XPath", xpath)
            for target in condition.calls:
                add_node("Template", target, {"name": target})
                add_edge("Condition", condition.id, "CALLS_TEMPLATE", "Template", target)

        return {
            "nodes": list(nodes.values()),
            "edges": [
                {
                    "from_kind": fk,
                    "from_key": fkey,
                    "relationship": rel,
                    "to_kind": tk,
                    "to_key": tkey,
                }
                for fk, fkey, rel, tk, tkey in sorted(edges)
            ],
            "parse_errors": self.parse_errors,
        }


class LineagePrinter:
    def __init__(self, graph: Dict) -> None:
        self.graph = graph
        self.nodes = {(n["kind"], n["key"]): n for n in graph["nodes"]}
        self.adj: Dict[Tuple[str, str], List[Tuple[str, str, str]]] = {}
        for edge in graph["edges"]:
            key = (edge["from_kind"], edge["from_key"])
            self.adj.setdefault(key, []).append((edge["relationship"], edge["to_kind"], edge["to_key"]))

    def print_lineage(self, field_name: str) -> None:
        start = ("Template", field_name)
        if start not in self.nodes:
            raise SystemExit(f"Template not found: {field_name}")
        print(field_name)
        self._walk(start, 1, set())

    def _walk(self, node_key: Tuple[str, str], level: int, visiting: Set[Tuple[str, str]]) -> None:
        if node_key in visiting:
            print("  " * level + "(cycle detected)")
            return
        visiting.add(node_key)
        for rel, to_kind, to_key in sorted(self.adj.get(node_key, []), key=lambda x: (x[0], x[1], x[2])):
            target_node = self.nodes.get((to_kind, to_key), {"key": to_key})
            label = self._display(target_node)
            print("  " * level + f"-> {rel} -> {label}")
            if to_kind in {"Template", "Variable", "Condition"}:
                self._walk((to_kind, to_key), level + 1, set(visiting))

    @staticmethod
    def _display(node: Dict) -> str:
        if node.get("kind") == "XPath":
            return node.get("expr", node.get("key", ""))
        if node.get("kind") == "Condition":
            test = node.get("test")
            kind = node.get("condition_kind")
            order = node.get("order")
            return f"{node.get('id')} [{kind} #{order}{' test=' + test if test else ''}]"
        return node.get("name") or node.get("path") or node.get("key", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse XSLT into graph JSON and optionally print lineage locally.")
    parser.add_argument("--root", required=True, help="Root XSLT file")
    parser.add_argument("--out", required=True, help="Output graph JSON file")
    parser.add_argument("--field", help="Optional field/template name to print lineage locally")
    args = parser.parse_args()

    builder = XsltGraphBuilder()
    builder.load(Path(args.root))
    graph = builder.build_graph()
    Path(args.out).write_text(json.dumps(graph, indent=2), encoding="utf-8")

    print(f"Graph written to: {args.out}")
    print(f"Nodes: {len(graph['nodes'])}")
    print(f"Edges: {len(graph['edges'])}")
    if graph["parse_errors"]:
        print("Parse warnings:")
        for err in graph["parse_errors"]:
            print(f"  - {err}")

    if args.field:
        print("\nLocal lineage:\n")
        LineagePrinter(graph).print_lineage(args.field)


if __name__ == "__main__":
    main()
