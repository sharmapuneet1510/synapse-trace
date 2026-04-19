#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Dict, List, Tuple

from neo4j import GraphDatabase


class Neo4jLineagePrinter:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def load_graph(self) -> Tuple[Dict[Tuple[str, str], Dict], Dict[Tuple[str, str], List[Tuple[str, str, str]]]]:
        nodes: Dict[Tuple[str, str], Dict] = {}
        adj: Dict[Tuple[str, str], List[Tuple[str, str, str]]] = {}
        with self.driver.session() as session:
            node_rows = session.run(
                "MATCH (n:XsltNode) RETURN n.kind AS kind, n.key AS key, properties(n) AS props"
            )
            for row in node_rows:
                kind = row["kind"]
                key = row["key"]
                props = dict(row["props"])
                props["kind"] = kind
                props["key"] = key
                nodes[(kind, key)] = props

            edge_rows = session.run(
                """
                MATCH (a:XsltNode)-[r:RELATES_TO]->(b:XsltNode)
                RETURN a.kind AS from_kind, a.key AS from_key, r.name AS rel, b.kind AS to_kind, b.key AS to_key
                """
            )
            for row in edge_rows:
                key = (row["from_kind"], row["from_key"])
                adj.setdefault(key, []).append((row["rel"], row["to_kind"], row["to_key"]))
        return nodes, adj

    def print_field_lineage(self, field_name: str) -> None:
        nodes, adj = self.load_graph()
        start = ("Template", field_name)
        if start not in nodes:
            raise SystemExit(f"Template not found in Neo4j: {field_name}")
        print(field_name)
        self._walk(nodes, adj, start, 1, set())

    def _walk(
        self,
        nodes: Dict[Tuple[str, str], Dict],
        adj: Dict[Tuple[str, str], List[Tuple[str, str, str]]],
        current: Tuple[str, str],
        level: int,
        visiting: set,
    ) -> None:
        if current in visiting:
            print("  " * level + "(cycle detected)")
            return
        visiting.add(current)
        for rel, to_kind, to_key in sorted(adj.get(current, []), key=lambda x: (x[0], x[1], x[2])):
            node = nodes.get((to_kind, to_key), {"kind": to_kind, "key": to_key})
            print("  " * level + f"-> {rel} -> {self._display(node)}")
            if to_kind in {"Template", "Variable", "Condition"}:
                self._walk(nodes, adj, (to_kind, to_key), level + 1, set(visiting))

    @staticmethod
    def _display(node: Dict) -> str:
        kind = node.get("kind")
        if kind == "XPath":
            return node.get("expr", node.get("key", ""))
        if kind == "Condition":
            test = node.get("test")
            condition_kind = node.get("condition_kind")
            order = node.get("order")
            return f"{node.get('id')} [{condition_kind} #{order}{' test=' + test if test else ''}]"
        return node.get("name") or node.get("path") or node.get("key", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Print lineage of one field/template from Neo4j")
    parser.add_argument("--field", required=True, help="Template/field name, for example T_EVENT_TIMESTAMP")
    parser.add_argument("--uri", required=True, help="Neo4j URI")
    parser.add_argument("--user", required=True, help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    args = parser.parse_args()

    printer = Neo4jLineagePrinter(args.uri, args.user, args.password)
    try:
        printer.print_field_lineage(args.field)
    finally:
        printer.close()


if __name__ == "__main__":
    main()
