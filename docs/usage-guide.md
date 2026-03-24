# Usage Guide

## Installation

```bash
cd synapse-trace
pip install -e .

# With Neo4j support
pip install -e ".[neo4j]"

# With dev/test tools
pip install -e ".[dev]"
```

---

## Single-Repository Mode

Point the parser at your Java and XSLT directories:

```bash
synapse-trace \
  --java-dirs src/main/java \
  --xslt-dirs src/main/resources/xslt \
  --output-dir output
```

Multiple directories per language are supported:

```bash
synapse-trace \
  --java-dirs src/main/java src/generated/java \
  --xslt-dirs src/main/resources/xslt config/transforms \
  --output-dir output
```

---

## Multi-Repository Mode

When your application depends on a shared library repo (e.g., a constants jar), you need to scan both repos together so Synapse Trace can link cross-repo references.

### Option 1: JSON Config File (Recommended)

Create a `repos.json`:

```json
{
  "repos": [
    {
      "name": "common-lib",
      "path": "/path/to/common-lib",
      "java_dirs": ["src/main/java"],
      "xslt_dirs": []
    },
    {
      "name": "trade-app",
      "path": "/path/to/trade-app",
      "java_dirs": ["src/main/java"],
      "xslt_dirs": ["src/main/resources/xslt"]
    },
    {
      "name": "settlement-app",
      "path": "/path/to/settlement-app",
      "java_dirs": ["src/main/java"],
      "xslt_dirs": ["src/main/resources/xslt", "config/transforms"]
    }
  ]
}
```

Run:

```bash
synapse-trace --config repos.json --output-dir output
```

### Option 2: Inline CLI

```bash
synapse-trace \
  --repo common-lib:/path/to/common-lib \
  --repo trade-app:/path/to/trade-app \
  --java-dirs src/main/java \
  --xslt-dirs src/main/resources/xslt
```

> **Note:** In inline mode, `--java-dirs` and `--xslt-dirs` are applied to every `--repo`. Use the JSON config file if repos have different directory layouts.

### How Directories Resolve

Paths in `java_dirs` and `xslt_dirs` can be relative or absolute:

- **Relative** (e.g., `src/main/java`) — resolved against the repo `path`
- **Absolute** (e.g., `/opt/sources/java`) — used as-is

Example: if `path` is `/repos/trade-app` and `java_dirs` is `["src/main/java"]`, the parser scans `/repos/trade-app/src/main/java`.

---

## Storage Providers

Control where the lineage graph is persisted with `--storages`:

```bash
# Default: PyVis HTML + JSON
synapse-trace --java-dirs src --xslt-dirs xslt --storages pyvis

# Both PyVis and Neo4j
synapse-trace --java-dirs src --xslt-dirs xslt --storages pyvis neo4j \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-user neo4j \
  --neo4j-password secret
```

| Provider | Output | Status |
|----------|--------|--------|
| `pyvis` | `lineage_graph.html` + `lineage_graph.json` | Fully implemented |
| `neo4j` | Direct Cypher persistence | Placeholder (JSON export + Cypher generation available) |

---

## Output Files

After a successful run, the `--output-dir` contains:

```
output/
├── lineage_graph.html            # Full graph — all fields, all repos
├── lineage_graph.json            # Full graph in Node-Link JSON
└── fields/
    ├── index.html                # Searchable field index page
    ├── N_EFFECTIVE_DATE.html     # Isolated lineage for this field
    ├── N_EFFECTIVE_DATE.json     # Isolated subgraph JSON
    ├── COUNTERPARTY_NAME.html
    ├── COUNTERPARTY_NAME.json
    ├── TRADE_STATUS.html
    ├── TRADE_STATUS.json
    └── ...                       # One HTML + JSON pair per field
```

| Path | Description |
|------|-------------|
| `lineage_graph.html` | Interactive visualization of the **full** lineage graph |
| `lineage_graph.json` | Full graph in Node-Link JSON (Neo4j APOC compatible) |
| `fields/index.html` | Searchable table listing every field with node/edge counts, types, repos, and links |
| `fields/{FIELD}.html` | **Isolated** lineage for a single field — only the nodes and edges connected to it |
| `fields/{FIELD}.json` | Isolated subgraph JSON — importable into Neo4j independently |

### Using the HTML Visualization

Open `lineage_graph.html` in any browser for the full graph. The control panel (top-right) provides:

- **Search** — Type a node name to highlight matches and dim everything else
- **Node Type Filters** — Toggle visibility of Java Classes, Methods, Fields, Constants, DTOs, XSLT Templates, XSLT Fields
- **Edge Type Filters** — Toggle Calls, Derived From, Transforms, Unmarshals To, Cross-Repo
- **Focus Mode** — Double-click any node to isolate its immediate neighborhood
- **Reset View** — Restore all nodes and edges
- **Fit All** — Zoom to fit the entire graph

### Per-Field Pages

Open `fields/index.html` to browse all fields. Each row shows:

- Field name, node count, edge count
- Color-coded badges for which node types participate (JAVA_FIELD, XSLT_FIELD, JAVA_CONSTANT, etc.)
- Cross-repo badge if the field spans multiple repositories
- Links to the isolated HTML visualization and raw JSON

Click any field name to open its dedicated page. Each per-field page:

- Shows **only** that field's lineage subgraph (no unrelated nodes)
- Has the same search/filter/focus controls as the full graph
- Links back to the field index and full graph

### Loading JSON into Neo4j

```cypher
-- Full graph
CALL apoc.import.json("file:///lineage_graph.json")

-- Single field only
CALL apoc.import.json("file:///fields/N_EFFECTIVE_DATE.json")

-- Or use the generated Cypher (programmatic)
-- See: neo4j_adapter.generate_cypher()
```

---

## Programmatic Usage

```python
from pathlib import Path
from orchestrator.models import RepoConfig, SynapseConfig  # noqa: E402
from orchestrator.parser import SynapseTracer

config = SynapseConfig(
    repos=[
        RepoConfig(
            name="common-lib",
            path=Path("/path/to/common-lib"),
            java_dirs=[Path("src/main/java")],
        ),
        RepoConfig(
            name="trade-app",
            path=Path("/path/to/trade-app"),
            java_dirs=[Path("src/main/java")],
            xslt_dirs=[Path("src/main/resources/xslt")],
        ),
    ],
    target_storages=["pyvis"],
    output_dir=Path("output"),
)

tracer = SynapseTracer(config)
lineage = tracer.trace()

# Inspect results
print(f"Nodes: {len(lineage.nodes)}, Edges: {len(lineage.edges)}")

for edge in lineage.edges:
    if edge.edge_type.value == "CROSS_REPO":
        print(f"  Cross-repo: {edge.source_id} -> {edge.target_id}")
```

---

## CLI Reference

```
synapse-trace [-h]
              [--config CONFIG]
              [--repo NAME:PATH]
              [--java-dirs DIR [DIR ...]]
              [--xslt-dirs DIR [DIR ...]]
              [--storages {pyvis,neo4j} [{pyvis,neo4j} ...]]
              [--output-dir DIR]
              [--neo4j-uri URI]
              [--neo4j-user USER]
              [--neo4j-password PASSWORD]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--config` | Path to JSON config with repos list | — |
| `--repo` | Inline repo definition `NAME:PATH` (repeatable) | — |
| `--java-dirs` | Java source directories | Required (single-repo) |
| `--xslt-dirs` | XSLT source directories | Required (single-repo) |
| `--storages` | Storage providers to use | `pyvis` |
| `--output-dir` | Output directory | `output` |
| `--neo4j-uri` | Neo4j bolt URI | — |
| `--neo4j-user` | Neo4j username | — |
| `--neo4j-password` | Neo4j password | — |
