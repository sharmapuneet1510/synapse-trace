# Synapse Trace

Data lineage tracer for Java/XSLT codebases with multi-provider graph storage.

Synapse Trace parses Java and XSLT source files, detects field mappings, constant references, DTO unmarshalling, and method calls, then **stitches** them into a unified lineage graph — even across multiple repositories.

## Quick Start

```bash
# Install
pip install -e .

# Single repo
synapse-trace \
  --java-dirs src/main/java \
  --xslt-dirs src/main/resources/xslt

# Multi-repo via config file
synapse-trace --config repos.json

# Output
open output/lineage_graph.html   # Interactive visualization
cat  output/lineage_graph.json   # Node-Link JSON (Neo4j compatible)
```

## Documentation

| Doc | Description |
|-----|-------------|
| [Usage Guide](docs/usage-guide.md) | CLI options, single-repo, multi-repo, config file format |
| [Parser Output](docs/parser-output.md) | What the parser produces — finding types, node/edge schemas, JSON format |
| [Architecture](docs/architecture.md) | Plugin system, provider interface, how stitching works |

## Project Structure

```
synapse-trace/
├── src/orchestrator/
│   ├── parser.py              # CLI entry point & orchestrator
│   ├── models.py              # Data models (nodes, edges, findings)
│   ├── stitcher.py            # Cross-language/cross-repo stitching
│   ├── parsers/
│   │   ├── java_parser.py     # Java source parser
│   │   └── xslt_parser.py     # XSLT parser
│   └── storage/
│       ├── base_provider.py   # Abstract provider interface
│       ├── local_graph_pyvis.py  # PyVis HTML visualizer
│       └── neo4j_adapter.py   # Neo4j placeholder + Cypher generator
├── tests/
│   ├── test_smoke.py
│   └── fixtures/              # Sample Java/XSLT for testing
├── docs/                      # Documentation
└── output/                    # Generated graphs
```

## Requirements

- Python >= 3.10
- networkx, pyvis, lxml (installed automatically)
- Optional: `neo4j` driver for direct Neo4j persistence
