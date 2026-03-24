# Architecture

## Design Principles

1. **Decouple parsing from storage** — Parsers produce findings, providers consume lineage. Neither knows about the other.
2. **Multi-repo first** — Every finding carries a `repo_name`. Cross-repo links are first-class edges.
3. **Plugin architecture** — New storage backends (Neo4j, S3, etc.) implement `BaseGraphProvider` without touching parser or stitcher code.

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    SynapseTracer                        │
│                    (parser.py)                          │
│                                                         │
│  ┌──────────┐  ┌──────────┐                             │
│  │ JavaParser│  │XsltParser│    Per-repo instances       │
│  │(repo_name)│  │(repo_name)│                            │
│  └─────┬─────┘  └─────┬─────┘                           │
│        │               │                                 │
│        ▼               ▼                                 │
│   JavaFinding[]   XsltFinding[]                          │
│        │               │                                 │
│        └───────┬───────┘                                 │
│                ▼                                         │
│         ┌────────────┐                                   │
│         │  Stitcher   │  Field normalization,            │
│         │             │  cross-repo matching             │
│         └──────┬──────┘                                  │
│                ▼                                         │
│        StitchedLineage                                   │
│        (nodes + edges)                                   │
│                │                                         │
│      ┌─────────┼──────────┐                              │
│      ▼         ▼          ▼                              │
│  ┌────────┐ ┌────────┐ ┌────────┐                       │
│  │ PyVis  │ │ Neo4j  │ │ Future │  BaseGraphProvider     │
│  │Provider│ │Adapter │ │Provider│  implementations       │
│  └───┬────┘ └───┬────┘ └───┬────┘                       │
│      │          │          │                             │
│      ▼          ▼          ▼                             │
│   .html      Cypher     (custom)                        │
│   .json      stmts                                      │
└─────────────────────────────────────────────────────────┘
```

---

## BaseGraphProvider Interface

All storage backends implement this abstract class:

```python
class BaseGraphProvider(ABC):

    @abstractmethod
    def add_node(self, node: LineageNode) -> None: ...

    @abstractmethod
    def add_edge(self, edge: LineageEdge) -> None: ...

    @abstractmethod
    def persist(self) -> None: ...

    @abstractmethod
    def export_node_link_json(self) -> dict: ...

    # Concrete convenience method (inherited by all providers):
    def ingest_lineage(self, lineage: StitchedLineage) -> None:
        for node in lineage.nodes:
            self.add_node(node)
        for edge in lineage.edges:
            self.add_edge(edge)
```

### Implementing a Custom Provider

```python
from orchestrator.storage.base_provider import BaseGraphProvider
from orchestrator.models import LineageNode, LineageEdge

class S3GraphProvider(BaseGraphProvider):
    def __init__(self, bucket: str, prefix: str):
        self._bucket = bucket
        self._nodes = []
        self._edges = []

    def add_node(self, node: LineageNode) -> None:
        self._nodes.append(node)

    def add_edge(self, edge: LineageEdge) -> None:
        self._edges.append(edge)

    def export_node_link_json(self) -> dict:
        # Build Node-Link schema dict
        ...

    def persist(self) -> None:
        # Upload JSON to S3
        import boto3
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=self._bucket,
            Key=f"{self._prefix}/lineage_graph.json",
            Body=json.dumps(self.export_node_link_json()),
        )
```

Register it in `parser.py`:

```python
from my_providers import S3GraphProvider

STORAGE_REGISTRY["s3"] = S3GraphProvider
```

---

## Stitching Algorithm

The stitcher is the core intelligence layer. It operates in two phases:

### Phase 1: Build Nodes and Intra-Language Edges

For each finding, create the appropriate graph node and edges within the same language:

- Java `method_call` → `JAVA_METHOD` node + `CALLS` edge from class
- Java `unmarshal` → `DTO` node + `UNMARSHALS_TO` edge from method
- Java `field_mapping` → `JAVA_FIELD` nodes + `DERIVED_FROM` edge (source → target)
- Java `constant_ref` → `JAVA_CONSTANT` node + `CALLS` edge from method
- Java `string_literal` → `JAVA_CONSTANT` node + `CALLS` edge from method
- XSLT `value_of` → `XSLT_FIELD` node + `TRANSFORMS` edge from template
- XSLT `template_call` → `CALLS` edge between templates

### Phase 2: Cross-Language and Cross-Repo Stitching

**Field matching** uses `_build_match_keys()` to generate all canonical forms of every field name:

```
"effectiveDate"               → {effectivedate, effective_date}
"N_EFFECTIVE_DATE"            → {n_effective_date, effective_date, effectivedate, neffectivedate}
"MessageKey.N_EFFECTIVE_DATE" → (strip qualifier) → same as N_EFFECTIVE_DATE
```

Both XSLT and Java findings are indexed by all their match keys. When the same key appears on both sides, a `DERIVED_FROM` (same repo) or `CROSS_REPO` (different repos) edge is created.

**DTO matching** links XSLT `template[@match]` to Java `unmarshal` targets when the DTO class name appears in the template's match pattern.

**Cross-repo constant matching** groups `constant_ref` and `string_literal` findings by their bare name across repos. When the same constant (e.g., `N_EFFECTIVE_DATE`) appears in two different repos, a `CROSS_REPO` edge links them.

---

## Data Models

All models are defined in `models.py` using Python `dataclass(slots=True)` for memory efficiency.

```
RepoConfig
├── name: str
├── path: Path
├── java_dirs: list[Path]
└── xslt_dirs: list[Path]

SynapseConfig
├── repos: list[RepoConfig]
├── target_storages: list[str]
├── output_dir: Path
└── neo4j_*: str

NodeMeta                          # FR-G2
├── file_path: str
├── line_number: int
├── code_snippet: str
└── md5_hash: str                 # auto-computed

JavaFinding / XsltFinding
├── (type-specific fields)
├── finding_type: str
├── meta: NodeMeta
└── repo_name: str

LineageNode
├── id: str
├── label: str
├── node_type: NodeType
├── meta: NodeMeta
└── properties: dict

LineageEdge
├── source_id: str
├── target_id: str
├── edge_type: EdgeType
└── properties: dict

StitchedLineage
├── nodes: list[LineageNode]
└── edges: list[LineageEdge]
```

---

## Parser Internals

### JavaParser

Uses compiled regex patterns against comment-stripped source. Maintains a brace-depth counter to track method scope:

1. Strip block comments (`/* ... */`), line comments (`// ...`), and string literals (`"..."`) from source
2. Scan line by line, tracking `current_package`, `current_class`, `current_method`
3. For each line, test against patterns in priority order: unmarshal > field_mapping > constant_ref > string_literal > method_call
4. Each match produces a `JavaFinding` with full metadata

**Limitations:**
- Regex-based — will miss patterns split across multiple lines
- Brace counting can be fooled by braces inside string literals or comments that weren't fully stripped
- Does not resolve imports — `MessageKey` is taken as-is without resolving to `com.bank.common.MessageKey`

### XsltParser

Uses `lxml.etree` for proper namespace-aware XML parsing:

1. Parse the file with `etree.parse()`
2. XPath query for `//xsl:template` with the XSLT namespace
3. Within each template, find `xsl:value-of`, `xsl:call-template`, `xsl:copy-of`
4. Extract field names from XPath `@select` expressions using `_extract_field_name()`
5. Determine the parent output element name for each `value-of`

**Field name extraction from XPath:**
- `order/customerName` → `customerName` (last path segment)
- `@id` → `id` (strip `@`)
- `ns:field[1]` → `field` (strip namespace prefix and predicates)
