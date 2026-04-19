#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from neo4j import GraphDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Load graph JSON into Neo4j")
    parser.add_argument("--graph", required=True, help="Graph JSON produced by xslt_to_graph.py")
    parser.add_argument("--uri", required=True, help="Neo4j URI, for example bolt://localhost:7687")
    parser.add_argument("--user", required=True, help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    parser.add_argument("--clear", action="store_true", help="Delete existing XSLT lineage nodes first")
    args = parser.parse_args()

    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))

    create_node_query = """
    MERGE (n:XsltNode {kind: $kind, key: $key})
    SET n += $props
    """

    create_edge_query = """
    MATCH (a:XsltNode {kind: $from_kind, key: $from_key})
    MATCH (b:XsltNode {kind: $to_kind, key: $to_key})
    MERGE (a)-[r:RELATES_TO {name: $relationship}]->(b)
    """

    with driver.session() as session:
        if args.clear:
            session.run("MATCH (n:XsltNode) DETACH DELETE n")

        for node in graph["nodes"]:
            props = dict(node)
            kind = props.pop("kind")
            key = props.pop("key")
            session.run(create_node_query, kind=kind, key=key, props=props)

        for edge in graph["edges"]:
            session.run(
                create_edge_query,
                from_kind=edge["from_kind"],
                from_key=edge["from_key"],
                to_kind=edge["to_kind"],
                to_key=edge["to_key"],
                relationship=edge["relationship"],
            )

    driver.close()
    print(f"Loaded {len(graph['nodes'])} nodes and {len(graph['edges'])} edges into Neo4j")


if __name__ == "__main__":
    main()
