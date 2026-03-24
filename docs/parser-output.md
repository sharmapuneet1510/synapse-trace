# Parser Output Reference

This document describes what the Synapse Trace parser produces at each stage of the pipeline: raw findings, stitched lineage graph, and the final output formats.

---

## Pipeline Overview

```
Java Files ──> JavaParser ──> JavaFinding[]  ─┐
                                               ├──> Stitcher ──> StitchedLineage ──> Providers
XSLT Files ──> XsltParser ──> XsltFinding[] ──┘                                      │
                                                                                      ├── lineage_graph.json
                                                                                      └── lineage_graph.html
```

---

## Stage 1: Raw Findings

### Java Findings

The `JavaParser` scans `.java` files and produces a list of `JavaFinding` objects. Each finding has a `finding_type` that describes what was detected.

| finding_type | What it detects | Example source code | Extracted fields |
|---|---|---|---|
| `field_mapping` | Setter/getter DTO mappings | `trade.setAmount(src.getAmount())` | `field_name="Amount"`, `target_field="Amount"`, `target_class="trade"` |
| `unmarshal` | DTO deserialization | `mapper.readValue(json, TradeDTO.class)` | `target_class="TradeDTO"` |
| `constant_ref` | Qualified constant references | `MessageKey.N_EFFECTIVE_DATE` | `field_name="N_EFFECTIVE_DATE"`, `target_class="MessageKey"` |
| `string_literal` | String keys that look like field names | `"N_EFFECTIVE_DATE"` | `field_name="N_EFFECTIVE_DATE"` |
| `method_call` | General method invocations | `service.validate(trade)` | `target_class="service"`, `target_field="validate"` |

**Constant Reference Detection Rules:**

The parser captures `Qualifier.CONSTANT_NAME` patterns where `CONSTANT_NAME` is at least 3 characters, all uppercase with underscores. Common false positives (`System.OUT`, `Integer.MAX_VALUE`, etc.) are filtered out.

**String Literal Detection Rules:**

Only string literals matching the pattern `"[A-Z][A-Z0-9_]{2,}"` are captured — at least 3 characters, uppercase with underscores. This targets field key constants like `"N_EFFECTIVE_DATE"` and ignores regular strings.

**Example JavaFinding:**

```python
JavaFinding(
    class_name="com.bank.trade.service.TradeService",
    method_name="processMessage",
    field_name="N_EFFECTIVE_DATE",
    finding_type="constant_ref",
    target_class="MessageKey",
    target_field="N_EFFECTIVE_DATE",
    meta=NodeMeta(
        file_path="app/src/main/java/TradeService.java",
        line_number=14,
        code_snippet='String effectiveDate = (String) message.get(MessageKey.N_EFFECTIVE_DATE);',
        md5_hash="a1b2c3d4e5f6..."
    ),
    repo_name="app-trade"
)
```

### XSLT Findings

The `XsltParser` scans `.xsl` and `.xslt` files using lxml for namespace-aware XML parsing.

| finding_type | What it detects | Example XSLT | Extracted fields |
|---|---|---|---|
| `value_of` | Field value extraction | `<xsl:value-of select="counterpartyName"/>` | `field_source="counterpartyName"`, `field_target="N_COUNTERPARTY_2"` (parent element) |
| `template_call` | Template invocation | `<xsl:call-template name="TradeMapping"/>` | `field_target="TradeMapping"` |
| `field_mapping` | Bulk copy operations | `<xsl:copy-of select="header/*"/>` | `field_source="header/*"` |

**Example XsltFinding:**

```python
XsltFinding(
    template_name="TradeOutput",
    template_match="TradeDTO",
    field_source="effectiveDate",
    field_target="N_EFFECTIVE_DATE",       # parent element name
    finding_type="value_of",
    meta=NodeMeta(
        file_path="app/src/main/resources/xslt/trade_output.xsl",
        line_number=8,
        code_snippet='<xsl:value-of select="effectiveDate"/>',
        md5_hash="f6e5d4c3b2a1..."
    ),
    repo_name="app-trade"
)
```

---

## Stage 2: Stitched Lineage

The `Stitcher` takes all Java and XSLT findings (from all repos) and builds a unified `StitchedLineage` containing nodes and edges.

### Node Types

| NodeType | Shape (in HTML) | Color | Description |
|---|---|---|---|
| `JAVA_CLASS` | Box | `#4A90D9` Blue | A Java class |
| `JAVA_METHOD` | Ellipse | `#7EC8E3` Light Blue | A method within a class |
| `JAVA_FIELD` | Diamond | `#A8D8EA` Pale Blue | A field involved in a setter/getter mapping |
| `JAVA_CONSTANT` | Square | `#E67E22` Orange | A constant reference (`MessageKey.N_EFFECTIVE_DATE`) or string literal (`"N_EFFECTIVE_DATE"`) |
| `DTO` | Hexagon | `#F5A623` Gold | A Data Transfer Object (target of unmarshal/readValue) |
| `XSLT_TEMPLATE` | Triangle | `#9B59B6` Purple | An `xsl:template` definition |
| `XSLT_FIELD` | Star | `#C39BD3` Light Purple | A field extracted via `xsl:value-of` |

### Node Properties (FR-G2 Metadata)

Every node carries rich metadata for Neo4j's Property Graph Model:

```json
{
  "id": "java::const::com.bank.trade.service.TradeService::MessageKey.N_EFFECTIVE_DATE",
  "label": "MessageKey.N_EFFECTIVE_DATE",
  "type": "JAVA_CONSTANT",
  "file_path": "app/src/main/java/TradeService.java",
  "line_number": 14,
  "code_snippet": "String effectiveDate = (String) message.get(MessageKey.N_EFFECTIVE_DATE);",
  "md5_hash": "a1b2c3d4e5f67890",
  "repo": "app-trade",
  "qualifier": "MessageKey",
  "bare_name": "N_EFFECTIVE_DATE"
}
```

### Edge Types (FR-G3)

| EdgeType | Color | Meaning | Example |
|---|---|---|---|
| `CALLS` | `#3498DB` Blue | Method invocation or template call | `TradeService.processMessage()` → `tradeRepo.save()` |
| `DERIVED_FROM` | `#E74C3C` Red | Data flows from source to target | XSLT `effectiveDate` → Java field `EffectiveDate` |
| `TRANSFORMS` | `#2ECC71` Green | XSLT template transforms a DTO or field | `XSLT:TradeOutput` → `DTO:TradeDTO` |
| `UNMARSHALS_TO` | `#F39C12` Yellow | Deserialization target | `processMessage()` → `DTO:TradeDTO` |
| `CROSS_REPO` | `#E91E63` Pink | Link between nodes from different repositories | XSLT field `effectiveDate` → lib constant `"EFFECTIVE_DATE"` |

### Field Name Variation Matching

The stitcher handles all common variations of the same logical field name. Given **any one** form, it generates all canonical forms for symmetric matching:

```
Input                              Match Keys Generated
─────────────────────────────      ──────────────────────────────
effectiveDate                  →   effectivedate, effective_date
N_EFFECTIVE_DATE               →   n_effective_date, neffectivedate,
                                   effective_date, effectivedate
MessageKey.N_EFFECTIVE_DATE    →   (strips qualifier, then same as above)
getEffectiveDate()             →   (strips "get" prefix, then same as above)
```

This means the following all resolve to the same lineage path:

| Layer | Code | Canonical match |
|---|---|---|
| XSLT select | `<xsl:value-of select="effectiveDate"/>` | `effectivedate` |
| XSLT output element | `<N_EFFECTIVE_DATE>` | `effective_date` |
| Java setter/getter | `trade.setEffectiveDate(src.getEffectiveDate())` | `effectivedate` |
| Java constant | `MessageKey.N_EFFECTIVE_DATE` | `effective_date` |
| Java string literal | `"N_EFFECTIVE_DATE"` | `effective_date` |
| Library constant definition | `public static final String N_EFFECTIVE_DATE = ...` | `effective_date` |

---

## Stage 3: Output Formats

### lineage_graph.json (Node-Link Schema)

The JSON output follows the [Node-Link](https://networkx.org/documentation/stable/reference/readwrite/generated/networkx.readwrite.json_graph.node_link_data.html) schema, which is directly importable by Neo4j APOC.

```json
{
  "directed": true,
  "multigraph": false,
  "graph": {},
  "nodes": [
    {
      "id": "java::class::com.bank.trade.service.TradeService",
      "label": "TradeService",
      "type": "JAVA_CLASS",
      "file_path": "",
      "line_number": 0,
      "code_snippet": "com.bank.trade.service.TradeService",
      "md5_hash": "ddaa3dd0272f...",
      "repo": "app-trade"
    },
    {
      "id": "xslt::field::TradeOutput::effectiveDate",
      "label": "N_EFFECTIVE_DATE",
      "type": "XSLT_FIELD",
      "file_path": "app-trade/xslt/trade_output.xsl",
      "line_number": 9,
      "code_snippet": "<xsl:value-of select=\"effectiveDate\"/>",
      "md5_hash": "f6e5d4c3b2a1...",
      "repo": "app-trade",
      "xpath": "effectiveDate",
      "output_element": "N_EFFECTIVE_DATE"
    }
  ],
  "links": [
    {
      "source": "xslt::field::TradeOutput::effectiveDate",
      "target": "java::literal::com.bank.common.FieldNames::EFFECTIVE_DATE",
      "type": "CROSS_REPO",
      "match_type": "field_name",
      "match_key": "effectivedate",
      "xslt_repo": "app-trade",
      "java_repo": "lib-common"
    },
    {
      "source": "xslt::TradeOutput",
      "target": "java::dto::TradeDTO",
      "type": "TRANSFORMS",
      "match_type": "dto_name",
      "xslt_repo": "app-trade",
      "java_repo": "app-trade"
    }
  ]
}
```

**Node ID Convention:**

```
{language}::{type}::{qualifier}::{name}

Examples:
  java::class::com.bank.trade.TradeService
  java::method::com.bank.trade.TradeService::processMessage
  java::field::com.bank.trade.TradeService::EffectiveDate
  java::const::com.bank.trade.TradeService::MessageKey.N_EFFECTIVE_DATE
  java::literal::com.bank.trade.TradeService::N_EFFECTIVE_DATE
  java::dto::TradeDTO
  xslt::TradeOutput
  xslt::field::TradeOutput::effectiveDate
```

### lineage_graph.html (Interactive Visualization)

A self-contained HTML file (no server needed) powered by [vis.js](https://visjs.org/) via PyVis. Features:

- **Dark theme** with color-coded nodes and edges
- **Search bar** — highlights matching nodes, dims the rest
- **Node type checkboxes** — toggle visibility per type (Java Class, Method, Field, Constant, DTO, XSLT Template, XSLT Field)
- **Edge type checkboxes** — toggle Calls, Derived From, Transforms, Unmarshals To, Cross-Repo
- **Focus mode** — double-click any node to isolate its neighborhood
- **Hover tooltips** — shows file path, line number, code snippet, MD5 hash
- **Physics-based layout** — Barnes-Hut force simulation for readability
- **Navigation buttons** — zoom, pan, fit all
- **Stats line** — shows visible node/edge count

### Per-Field Isolated Views (fields/ directory)

Every field detected in the lineage gets its own standalone HTML page and JSON file. This lets you examine a single field's complete lineage path without the noise of the full graph.

```
output/
├── lineage_graph.html          # Full graph (all fields)
├── lineage_graph.json
└── fields/
    ├── index.html              # Field index — searchable table linking to all fields
    ├── N_EFFECTIVE_DATE.html   # Isolated lineage for N_EFFECTIVE_DATE
    ├── N_EFFECTIVE_DATE.json
    ├── COUNTERPARTY_NAME.html
    ├── COUNTERPARTY_NAME.json
    ├── TRADE_STATUS.html
    ├── TRADE_STATUS.json
    └── ...                     # One pair per field
```

**Field Index** (`fields/index.html`):

A searchable table listing every field with:

| Column | Description |
|--------|-------------|
| Field | Field name (links to its isolated HTML page) |
| Nodes | Number of nodes in the field's subgraph |
| Edges | Number of edges in the field's subgraph |
| Types | Color-coded badges showing which node types appear (JAVA_FIELD, XSLT_FIELD, JAVA_CONSTANT, etc.) |
| Repos | Which repositories contribute to this field's lineage |
| Links | Quick links to the HTML visualization and raw JSON |

The index page has a filter input at the top — type any part of a field name to narrow the list.

**Per-Field HTML** (e.g., `fields/N_EFFECTIVE_DATE.html`):

Each field page is a fully interactive graph (same controls as the full graph) showing only the nodes and edges that are part of that field's lineage. It includes:

- Navigation links back to the Field Index and Full Graph
- The same search, filter, focus, and reset controls as the full graph
- Only the subgraph relevant to that specific field

**Per-Field JSON** (e.g., `fields/N_EFFECTIVE_DATE.json`):

Same Node-Link schema as the full JSON, but containing only the nodes and edges for that field. Can be imported into Neo4j independently.

**How fields are identified:**

A "field" is any node of type XSLT_FIELD, JAVA_FIELD, or JAVA_CONSTANT. Its isolated subgraph is built by walking all connected nodes from that seed node (BFS up to 10 hops), collecting every node and edge that participates in that field's lineage path.

**Example:** `fields/TRADE_STATUS.json` for a field that only exists as a cross-repo constant:

```json
{
  "directed": true,
  "multigraph": false,
  "graph": {},
  "nodes": [
    {
      "id": "java::literal::com.bank.common.FieldNames::TRADE_STATUS",
      "label": "\"TRADE_STATUS\"",
      "type": "JAVA_CONSTANT",
      "repo": "lib-common",
      "bare_name": "TRADE_STATUS"
    },
    {
      "id": "java::literal::com.bank.trade.service.TradeService::TRADE_STATUS",
      "label": "\"TRADE_STATUS\"",
      "type": "JAVA_CONSTANT",
      "repo": "app-trade",
      "bare_name": "TRADE_STATUS"
    }
  ],
  "links": [
    {
      "source": "java::literal::com.bank.common.FieldNames::TRADE_STATUS",
      "target": "java::literal::com.bank.trade.service.TradeService::TRADE_STATUS",
      "type": "CROSS_REPO",
      "match_type": "cross_repo_constant",
      "repo_a": "lib-common",
      "repo_b": "app-trade"
    }
  ]
}
```

---

## Example: Tracing a Field End-to-End

Given `N_EFFECTIVE_DATE`, open `fields/N_EFFECTIVE_DATE.html` to see its isolated lineage, or trace it in the full graph:

```
XSLT Template: TradeOutput (match="TradeDTO")
    │
    │  TRANSFORMS
    ▼
XSLT Field: effectiveDate → <N_EFFECTIVE_DATE>
    │
    │  DERIVED_FROM (match_key: "effectivedate")
    ▼
Java Field: TradeService.setEffectiveDate(src.getEffectiveDate())
    │
    │  DERIVED_FROM (match_key: "effective_date")
    ▼
Java Constant: MessageKey.N_EFFECTIVE_DATE  [app-trade repo]
    │
    │  CROSS_REPO (match_key: "n_effective_date")
    ▼
Java String Literal: "N_EFFECTIVE_DATE"  [lib-common repo]
```

This path is visible in:
- **Full graph** (`lineage_graph.html`) — as a connected subgraph within the larger visualization
- **Isolated view** (`fields/N_EFFECTIVE_DATE.html`) — as a standalone page with only this field's nodes
- **JSON** (`fields/N_EFFECTIVE_DATE.json`) — importable into Neo4j independently
