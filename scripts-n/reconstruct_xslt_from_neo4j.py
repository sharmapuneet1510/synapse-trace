#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import List, Dict, Set
from neo4j import GraphDatabase


def escape_xml_attr(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


class Neo4jXsltReconstructor:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def reconstruct(self, template_name: str, include_variables: bool = True) -> str:
        with self.driver.session() as session:
            template = session.run(
                """
                MATCH (t:XsltNode {kind:'Template', name:$name})
                RETURN properties(t) AS t
                """,
                name=template_name,
            ).single()

            if not template:
                raise ValueError(f"Template not found: {template_name}")

            conditions = session.run(
                """
                MATCH (t:XsltNode {kind:'Template', name:$name})
                      -[:RELATES_TO {name:'HAS_CONDITION'}]->
                      (c:XsltNode {kind:'Condition'})
                RETURN properties(c) AS c
                ORDER BY c.order ASC, c.key ASC
                """,
                name=template_name,
            ).data()

            direct_xpaths = session.run(
                """
                MATCH (t:XsltNode {kind:'Template', name:$name})
                      -[:RELATES_TO {name:'USES_XPATH'}]->
                      (x:XsltNode {kind:'XPath'})
                RETURN DISTINCT x.expr AS expr
                ORDER BY x.expr
                """,
                name=template_name,
            ).data()

            direct_calls = session.run(
                """
                MATCH (t:XsltNode {kind:'Template', name:$name})
                      -[:RELATES_TO {name:'CALLS_TEMPLATE'}]->
                      (c:XsltNode {kind:'Template'})
                RETURN DISTINCT c.name AS name
                ORDER BY c.name
                """,
                name=template_name,
            ).data()

            lines: List[str] = []
            lines.append(f'<xsl:template name="{template_name}">')

            if conditions:
                lines.append("  <xsl:choose>")

                for row in conditions:
                    c = dict(row["c"])
                    condition_key = c["key"]
                    cond_type = c.get("condition_kind", "when")
                    cond_test = c.get("test", "")
                    order = c.get("order")

                    if cond_type == "when":
                        lines.append(f'    <xsl:when test="{escape_xml_attr(cond_test)}">')
                    else:
                        lines.append("    <xsl:otherwise>")

                    selected_xpaths = session.run(
                        """
                        MATCH (c:XsltNode {kind:'Condition', key:$key})
                              -[:RELATES_TO {name:'SELECTS_XPATH'}]->
                              (x:XsltNode {kind:'XPath'})
                        RETURN DISTINCT x.expr AS expr
                        ORDER BY x.expr
                        """,
                        key=condition_key,
                    ).data()

                    used_variables = session.run(
                        """
                        MATCH (c:XsltNode {kind:'Condition', key:$key})
                              -[:RELATES_TO {name:'USES_VARIABLE'}]->
                              (v:XsltNode {kind:'Variable'})
                        RETURN DISTINCT v.name AS name
                        ORDER BY v.name
                        """,
                        key=condition_key,
                    ).data()

                    called_templates = session.run(
                        """
                        MATCH (c:XsltNode {kind:'Condition', key:$key})
                              -[:RELATES_TO {name:'CALLS_TEMPLATE'}]->
                              (t:XsltNode {kind:'Template'})
                        RETURN DISTINCT t.name AS name
                        ORDER BY t.name
                        """,
                        key=condition_key,
                    ).data()

                    if used_variables:
                        lines.append(f'      <!-- condition order: {order} -->')
                        for v in used_variables:
                            lines.append(f'      <!-- uses variable: ${v["name"]} -->')

                    for x in selected_xpaths:
                        lines.append(f'      <xsl:value-of select="{escape_xml_attr(x["expr"])}"/>')

                    for t in called_templates:
                        lines.append(f'      <xsl:call-template name="{escape_xml_attr(t["name"])}"/>')

                    if cond_type == "when":
                        lines.append("    </xsl:when>")
                    else:
                        lines.append("    </xsl:otherwise>")

                lines.append("  </xsl:choose>")
            else:
                for x in direct_xpaths:
                    lines.append(f'  <xsl:value-of select="{escape_xml_attr(x["expr"])}"/>')

                for c in direct_calls:
                    lines.append(f'  <xsl:call-template name="{escape_xml_attr(c["name"])}"/>')

            lines.append("</xsl:template>")

            if include_variables:
                lines.append("")
                lines.append("<!-- Variable Definitions -->")
                lines.append("")

                for var in self._collect_variables_for_template(session, template_name):
                    expr = var.get("select") or var.get("text") or ""
                    if expr:
                        lines.append(
                            f'<xsl:variable name="{escape_xml_attr(var["name"])}" '
                            f'select="{escape_xml_attr(expr)}"/>'
                        )
                    else:
                        lines.append(f'<xsl:variable name="{escape_xml_attr(var["name"])}"/>')

            return "\n".join(lines)

    def _collect_variables_for_template(self, session, template_name: str) -> List[Dict]:
        rows = session.run(
            """
            MATCH p = (t:XsltNode {kind:'Template', name:$name})
                      -[:RELATES_TO*]->
                      (v:XsltNode {kind:'Variable'})
            RETURN DISTINCT properties(v) AS v
            ORDER BY v.name
            """,
            name=template_name,
        ).data()

        result: List[Dict] = []
        seen: Set[str] = set()
        for row in rows:
            var = dict(row["v"])
            name = var.get("name")
            if name and name not in seen:
                seen.add(name)
                result.append(var)
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--field", required=True, help="Template/field name, for example T_EVENT_TIMESTAMP")
    parser.add_argument("--uri", required=True, help="Neo4j URI, for example bolt://localhost:7687")
    parser.add_argument("--user", required=True, help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    parser.add_argument("--out", help="Optional output file path")
    parser.add_argument("--no-variables", action="store_true", help="Do not print variable definitions")
    args = parser.parse_args()

    reconstructor = Neo4jXsltReconstructor(args.uri, args.user, args.password)
    try:
        code = reconstructor.reconstruct(args.field, include_variables=not args.no_variables)
    finally:
        reconstructor.close()

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Reconstructed code written to: {args.out}")
    else:
        print(code)


if __name__ == "__main__":
    main()
