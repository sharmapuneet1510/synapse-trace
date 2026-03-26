# Variable Trace — Examples & Integration Guide

The variable trace system finds all code entities (Java classes, methods, constants, XSLT templates, fields) connected to a given field name, across the full parsed lineage graph, and returns them as a subgraph for display or further analysis.

---

## Table of Contents

1. [How Name Matching Works](#how-name-matching-works)
2. [REST API Examples](#rest-api-examples)
3. [Python (Backend Direct)](#python-backend-direct)
4. [Frontend TypeScript Examples](#frontend-typescript-examples)
5. [Reading the TraceResponse](#reading-the-traceresponse)
6. [Interpreting the Graph](#interpreting-the-graph)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## How Name Matching Works

When you submit `N_EFFECTIVE_DATE`, the system automatically expands it into all canonical forms before searching:

| Input | Auto-derived variants |
|-------|-----------------------|
| `N_EFFECTIVE_DATE` | `n_effective_date`, `nEffectiveDate`, `EFFECTIVE_DATE`, `effective_date`, `effectiveDate` |
| `effectiveDate` | `EFFECTIVE_DATE`, `effective_date`, `N_EFFECTIVE_DATE`, `nEffectiveDate` |
| `TradeMapper` | `trade_mapper`, `TRADE_MAPPER`, `tradeMapper` |

The matching rules:
1. **Lowercase normalize** — compared case-insensitively
2. **camelCase → UPPER_SNAKE** bidirectional conversion
3. **Prefix stripping** — single-letter prefixes (`N_`, `S_`, `B_`, `D_`, `I_`, `L_`) are stripped, then the bare name is also matched
4. **Underscore removal** — `EFFECTIVE_DATE` is also tested as `effectivedate` for substring matching

This means you can type the Java constant name, the camelCase getter name, or the XSLT field name — and the trace will find all of them.

**Additional variations** let you supply domain-specific aliases the system cannot derive:

```json
{
  "variable_name": "N_EFFECTIVE_DATE",
  "jurisdiction_id": "hkma",
  "additional_variations": ["effectiveDt", "effDate", "TRADE_EFFECTIVE_DATE"]
}
```

---

## REST API Examples

### Example 1 — Basic trace, single field

```bash
curl -X POST http://localhost:8000/api/trace/variable \
  -H "Content-Type: application/json" \
  -d '{
    "variable_name": "N_EFFECTIVE_DATE",
    "jurisdiction_id": "hkma"
  }'
```

**Response:**

```json
{
  "variable_name": "N_EFFECTIVE_DATE",
  "jurisdiction_id": "hkma",
  "variations_searched": [
    "n_effective_date",
    "neffectivedate",
    "neffective_date",
    "effective_date",
    "effectivedate",
    "nEffectiveDate",
    "EFFECTIVE_DATE",
    "effectiveDate",
    "N_EFFECTIVE_DATE"
  ],
  "nodes": [
    {
      "id": "java::constant::com.bank.hkma.MessageKey::N_EFFECTIVE_DATE",
      "label": "N_EFFECTIVE_DATE",
      "node_type": "JAVA_CONSTANT",
      "file_path": "/repos/hkma-reporting/src/main/java/com/bank/hkma/MessageKey.java",
      "line_number": 23,
      "code_snippet": "public static final String N_EFFECTIVE_DATE = \"N_EFFECTIVE_DATE\";",
      "properties": {}
    },
    {
      "id": "java::method::com.bank.hkma.TradeMapper::mapTradeStateFields",
      "label": "mapTradeStateFields",
      "node_type": "JAVA_METHOD",
      "file_path": "/repos/hkma-reporting/src/main/java/com/bank/hkma/TradeMapper.java",
      "line_number": 115,
      "code_snippet": "map.put(MessageKey.N_EFFECTIVE_DATE, trade.getEffectiveDate());",
      "properties": {}
    },
    {
      "id": "xslt::field::trade_state.xsl::effectiveDate",
      "label": "effectiveDate",
      "node_type": "XSLT_FIELD",
      "file_path": "/repos/hkma-reporting/src/main/resources/xslt/trade_state.xsl",
      "line_number": 88,
      "code_snippet": "<xsl:value-of select=\"tradeHeader/effectiveDate\"/>",
      "properties": {}
    },
    {
      "id": "xslt::template::trade_state.xsl::TradeStateTemplate",
      "label": "TradeStateTemplate",
      "node_type": "XSLT_TEMPLATE",
      "file_path": "/repos/hkma-reporting/src/main/resources/xslt/trade_state.xsl",
      "line_number": 12,
      "code_snippet": "<xsl:template name=\"TradeStateTemplate\">",
      "properties": {}
    }
  ],
  "edges": [
    {
      "source": "java::method::com.bank.hkma.TradeMapper::mapTradeStateFields",
      "target": "java::constant::com.bank.hkma.MessageKey::N_EFFECTIVE_DATE",
      "type": "DERIVED_FROM",
      "properties": {}
    },
    {
      "source": "xslt::template::trade_state.xsl::TradeStateTemplate",
      "target": "xslt::field::trade_state.xsl::effectiveDate",
      "type": "TRANSFORMS",
      "properties": {}
    }
  ],
  "node_count": 4,
  "edge_count": 2,
  "parse_status": "ready"
}
```

---

### Example 2 — Trace with extra aliases

Useful when a field has legacy names or non-standard abbreviations in the codebase.

```bash
curl -X POST http://localhost:8000/api/trace/variable \
  -H "Content-Type: application/json" \
  -d '{
    "variable_name": "N_NOTIONAL_AMOUNT",
    "jurisdiction_id": "mas",
    "additional_variations": ["notionalAmt", "NOTIONAL", "tradeNotional"],
    "max_depth": 10
  }'
```

---

### Example 3 — Shallow trace (max_depth=2)

Limits BFS to immediate neighbours only — faster, fewer nodes returned.

```bash
curl -X POST http://localhost:8000/api/trace/variable \
  -H "Content-Type: application/json" \
  -d '{
    "variable_name": "N_TRADE_ID",
    "jurisdiction_id": "dtcc",
    "max_depth": 2
  }'
```

---

### Example 4 — Check parse status before tracing

If `parse_status` is not `"ready"`, trace results will be empty. Check first:

```bash
curl http://localhost:8000/api/parse/status
```

```json
{
  "batch_status": "done",
  "jurisdictions": {
    "hkma": { "status": "ready", "nodes": 120, "edges": 95 },
    "mas":  { "status": "pending" }
  }
}
```

Only trace jurisdictions with `"status": "ready"`.

---

### Example 5 — Variable not found

When the variable has no matching nodes (parse is ready but the name doesn't exist in the graph):

```json
{
  "variable_name": "N_NONEXISTENT_FIELD",
  "jurisdiction_id": "hkma",
  "variations_searched": ["n_nonexistent_field", "nonexistentField", ...],
  "nodes": [],
  "edges": [],
  "node_count": 0,
  "edge_count": 0,
  "parse_status": "ready"
}
```

**Resolution steps:**
1. Confirm the field name exists in `jurisdiction.json`
2. Check if the field has a different prefix in the codebase (try `additional_variations`)
3. Verify the jurisdiction's parse completed without errors

---

## Python (Backend Direct)

Call the trace service directly without the HTTP layer — useful for scripts, notebooks, or batch analysis.

### Basic usage

```python
from src.api.services.trace_service import trace_variable

result = trace_variable(
    variable_name="N_EFFECTIVE_DATE",
    jurisdiction_id="hkma",
)

print(f"Found {result.node_count} nodes, {result.edge_count} edges")
print(f"Variations searched: {result.variations_searched}")

for node in result.nodes:
    print(f"  [{node.node_type}] {node.label} — {node.file_path}:{node.line_number}")
```

### With additional variations

```python
result = trace_variable(
    variable_name="N_EFFECTIVE_DATE",
    jurisdiction_id="hkma",
    additional_variations=["effectiveDt", "TRADE_EFFECTIVE_DATE"],
    max_depth=10,
)
```

### Export to a simple dict for JSON output

```python
import json

output = {
    "variable": result.variable_name,
    "jurisdiction": result.jurisdiction_id,
    "node_count": result.node_count,
    "edge_count": result.edge_count,
    "nodes": [
        {
            "id": n.id,
            "label": n.label,
            "type": n.node_type,
            "file": n.file_path,
            "line": n.line_number,
        }
        for n in result.nodes
    ],
    "edges": [
        {"from": e.source, "to": e.target, "type": e.type}
        for e in result.edges
    ],
}

print(json.dumps(output, indent=2))
```

### Ensure parse is ready first

```python
from src.api.services.cache import parse_cache

cache = parse_cache.get("hkma")
if not cache or cache.status != "ready":
    raise RuntimeError("HKMA parse not ready — trigger a batch parse first")

result = trace_variable("N_EFFECTIVE_DATE", "hkma")
```

### Using quick_trace.py (standalone — no API server needed)

```python
from src.orchestrator.quick_trace import trace_project

# Run a full trace from scratch (does not use ParseCache)
result = trace_project(
    main="/repos/hkma-reporting",
    libs=["/repos/hkma-common-lib"],
)

# Filter to a single variable
subset = result.filter("N_EFFECTIVE_DATE")
subset.print_summary()
# Nodes: 4  Edges: 2
# Java findings: 18  XSLT findings: 7

# Export the filtered subgraph
subset.to_json("output/effective_date_lineage.json")
subset.to_html("output/effective_date_lineage.html")  # interactive PyVis graph
```

---

## Frontend TypeScript Examples

### Run a trace from a React component

```typescript
import { useTraceVariable } from '../../hooks/useTrace';
import { useState } from 'react';
import type { TraceResponse } from '../../types/trace';

export default function MyTraceComponent() {
  const [result, setResult] = useState<TraceResponse | null>(null);
  const traceMutation = useTraceVariable();

  const handleTrace = () => {
    traceMutation.mutate(
      {
        variable_name: 'N_EFFECTIVE_DATE',
        jurisdiction_id: 'hkma',
        additional_variations: ['effectiveDt'],
        max_depth: 15,
      },
      { onSuccess: (data) => setResult(data) }
    );
  };

  return (
    <div>
      <button onClick={handleTrace} disabled={traceMutation.isPending}>
        {traceMutation.isPending ? 'Tracing...' : 'Trace'}
      </button>
      {result && (
        <p>
          Found {result.node_count} nodes and {result.edge_count} edges.
          Status: {result.parse_status}
        </p>
      )}
    </div>
  );
}
```

### Call the trace API directly (without hooks)

```typescript
import { traceVariable } from '../../api/trace';

const result = await traceVariable({
  variable_name: 'N_NOTIONAL_AMOUNT',
  jurisdiction_id: 'mas',
  additional_variations: ['notionalAmt'],
  max_depth: 12,
});

console.log('Searched variations:', result.variations_searched);
console.log('Nodes:', result.nodes.map(n => `${n.node_type}: ${n.label}`));
```

### Filter nodes by type

```typescript
const javaNodes = result.nodes.filter(n => n.node_type.startsWith('JAVA_'));
const xsltNodes = result.nodes.filter(n => n.node_type.startsWith('XSLT_'));
const constants = result.nodes.filter(n => n.node_type === 'JAVA_CONSTANT');
```

### Build an adjacency list from edges

```typescript
const adjacency = new Map<string, string[]>();
for (const edge of result.edges) {
  if (!adjacency.has(edge.source)) adjacency.set(edge.source, []);
  adjacency.get(edge.source)!.push(edge.target);
}
```

---

## Reading the TraceResponse

```typescript
interface TraceResponse {
  variable_name: string;       // The name you submitted
  jurisdiction_id: string;     // The jurisdiction you searched
  variations_searched: string[]; // All auto-derived + extra aliases searched
  nodes: TraceNode[];          // All connected code entities
  edges: TraceEdge[];          // Directed relationships between nodes
  node_count: number;          // == nodes.length
  edge_count: number;          // == edges.length
  parse_status: string;        // "ready" | "not_parsed" | "error"
}

interface TraceNode {
  id: string;           // Unique stable ID: "java::constant::com.bank.MessageKey::N_EFFECTIVE_DATE"
  label: string;        // Short display name: "N_EFFECTIVE_DATE"
  node_type: string;    // JAVA_CLASS | JAVA_METHOD | JAVA_FIELD | JAVA_CONSTANT | DTO | XSLT_FILE | XSLT_TEMPLATE | XSLT_FIELD
  file_path?: string;   // Absolute path to source file
  line_number?: number; // Line number in source file
  code_snippet?: string; // Relevant code extract (may be multi-line)
  properties: Record<string, unknown>; // Additional metadata
}

interface TraceEdge {
  source: string;   // Source node ID
  target: string;   // Target node ID
  type: string;     // CALLS | DERIVED_FROM | TRANSFORMS | LOADS_XSLT | CROSS_REPO | UNMARSHALS_TO
  properties: Record<string, unknown>;
}
```

### Node ID format

Node IDs follow the pattern `{language}::{entity_type}::{qualified_name}`:

| Example ID | Interpretation |
|------------|----------------|
| `java::class::com.bank.TradeMapper` | Java class `TradeMapper` in package `com.bank` |
| `java::method::com.bank.TradeMapper::mapFields` | Method `mapFields` on `TradeMapper` |
| `java::constant::com.bank.MessageKey::N_EFFECTIVE_DATE` | Constant `N_EFFECTIVE_DATE` on `MessageKey` |
| `xslt::file::trade_state.xsl` | XSLT stylesheet file |
| `xslt::template::trade_state.xsl::TradeStateTemplate` | Named template inside a stylesheet |
| `xslt::field::trade_state.xsl::effectiveDate` | Field reference inside a template |

---

## Interpreting the Graph

### Reading edge direction

Edges are **directed**: `source → target`. The direction follows the data/call flow:

| Edge type | Reads as |
|-----------|----------|
| `DERIVED_FROM` | source value is derived from target |
| `CALLS` | source method calls target method |
| `TRANSFORMS` | source (template) transforms target (field) |
| `LOADS_XSLT` | source (Java) loads target (XSLT file) |
| `UNMARSHALS_TO` | source (Java method) unmarshals into target (DTO) |
| `CROSS_REPO` | source in main repo references target in library repo |

### Finding the full path from Java to XSLT

To trace how data flows from a Java class through to the XSLT output:

1. Find nodes with `node_type: "JAVA_CONSTANT"` — these are the field key definitions
2. Follow `DERIVED_FROM` edges to find which methods use this constant
3. Follow `LOADS_XSLT` edges from those methods to `XSLT_FILE` nodes
4. Follow `TRANSFORMS` edges to find `XSLT_TEMPLATE` and `XSLT_FIELD` nodes

### Cross-repo relationships

`CROSS_REPO` edges indicate the field appears in both the main reporting repository (`git_path`) and the shared library (`lib_path`). This is common for field key constants that are defined once in a library and referenced across many reporting modules.

---

## Common Patterns

### "I see only XSLT nodes — no Java"

- The Java code may not reference this field by the expected constant name
- Try `additional_variations` with the setter/getter name: `getEffectiveDate`, `setEffectiveDate`
- Check if the field is referenced via a string literal in Java: `"N_EFFECTIVE_DATE"` — these are captured as `JAVA_FIELD` or `JAVA_CONSTANT` nodes depending on context

### "I see only Java nodes — no XSLT"

- The XSLT may use a different XPath expression not matched by the canonical key
- Try `additional_variations` with the raw XPath element name from the XSLT file

### "node_count is 0 but parse_status is ready"

- The field name may not exist in this jurisdiction's codebase
- Try a broader name variant
- Confirm the field actually appears in the `configs` section of `jurisdiction.json` for this jurisdiction

### "parse_status is not_parsed"

- Trigger a batch parse from the Dashboard
- Wait for the status to show `ready` for the target jurisdiction

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| HTTP 500 on trace | Parse cache not loaded | Restart backend; trigger a parse |
| `node_count: 0`, `parse_status: ready` | Variable not in graph | Try `additional_variations` or check spelling |
| `parse_status: not_parsed` | Parse not run for this jurisdiction | Trigger parse from Dashboard |
| Same nodes every trace, no matter the input | Bug in match keys | Check `_build_match_keys()` in `stitcher.py` |
| Graph shows too many unrelated nodes | `max_depth` too high | Lower `max_depth` to 3–5 |
| Very slow trace response | Large graph + high `max_depth` | Lower `max_depth`; consider pagination |
