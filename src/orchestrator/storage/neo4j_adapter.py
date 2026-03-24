"""Neo4j graph provider — placeholder for future implementation.

Export the lineage as Node-Link JSON and use Neo4j APOC `apoc.import.json`
or the included Cypher generation to load into a Neo4j instance.
"""

from __future__ import annotations

from orchestrator.models import LineageEdge, LineageNode
from orchestrator.storage.base_provider import BaseGraphProvider


class Neo4jGraphProvider(BaseGraphProvider):
    """Future-ready Neo4j adapter.

    Currently stores nodes/edges in memory and can generate Cypher statements.
    Full driver-based persistence will be added when neo4j is needed.
    """

    def __init__(
        self,
        uri: str = "",
        user: str = "",
        password: str = "",
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._nodes: list[LineageNode] = []
        self._edges: list[LineageEdge] = []

    def add_node(self, node: LineageNode) -> None:
        self._nodes.append(node)

    def add_edge(self, edge: LineageEdge) -> None:
        self._edges.append(edge)

    def export_node_link_json(self) -> dict:
        nodes = []
        for n in self._nodes:
            nodes.append({
                "id": n.id,
                "label": n.label,
                "type": n.node_type.value,
                "file_path": n.meta.file_path,
                "line_number": n.meta.line_number,
                "code_snippet": n.meta.code_snippet,
                "md5_hash": n.meta.md5_hash,
                **n.properties,
            })
        links = []
        for e in self._edges:
            links.append({
                "source": e.source_id,
                "target": e.target_id,
                "type": e.edge_type.value,
                **e.properties,
            })
        return {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": nodes,
            "links": links,
        }

    def generate_cypher(self) -> str:
        """Generate Cypher CREATE/MERGE statements for loading into Neo4j."""
        lines: list[str] = []
        for n in self._nodes:
            props = {
                "id": n.id,
                "label": n.label,
                "file_path": n.meta.file_path,
                "line_number": n.meta.line_number,
                "code_snippet": n.meta.code_snippet,
                "md5_hash": n.meta.md5_hash,
                **n.properties,
            }
            prop_str = ", ".join(f"{k}: {_cypher_val(v)}" for k, v in props.items())
            lines.append(
                f"MERGE (n:{n.node_type.value} {{{prop_str}}});"
            )
        for e in self._edges:
            props = {**e.properties}
            prop_str = ""
            if props:
                prop_str = " {" + ", ".join(f"{k}: {_cypher_val(v)}" for k, v in props.items()) + "}"
            lines.append(
                f"MATCH (a {{id: {_cypher_val(e.source_id)}}}), "
                f"(b {{id: {_cypher_val(e.target_id)}}}) "
                f"MERGE (a)-[:{e.edge_type.value}{prop_str}]->(b);"
            )
        return "\n".join(lines)

    def persist(self) -> None:
        if not self._uri:
            raise NotImplementedError(
                "Neo4j adapter requires a URI. Set neo4j_uri in config, or "
                "use export_node_link_json() / generate_cypher() for offline loading."
            )
        # Future: use neo4j driver to execute self.generate_cypher()
        raise NotImplementedError(
            "Direct Neo4j driver persistence not yet implemented. "
            "Use generate_cypher() or export JSON with export_node_link_json() "
            "and load via APOC apoc.import.json."
        )


def _cypher_val(v: object) -> str:
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return f"'{v}'"
