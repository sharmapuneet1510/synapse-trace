# Data Lineage Platform – Requirement Specification (v3)

## 1. Objective

Build a **field-level Data Lineage Platform** that enables users to:

- Trace the complete derivation of a field.
- Understand how and why a value is generated.
- Visualize the end-to-end transformation pipeline.
- Explore branching logic as a pipeline with conditional branches or a mind-map style graph.
- Provide audit-ready traceability across **XSLT and Java codebases**.
- Support local graph generation first, without requiring Neo4j in v1.

This platform is intended to behave as a **logic intelligence engine for regulatory fields**.

---

## 2. Scope

### 2.1 Included in v1

- Field-by-field lineage tracing.
- Multi-repo support.
- Maven-based project scanning.
- Java 8 to 17+ source support.
- XSLT parsing with heavy support for:
  - `xsl:call-template`
  - `xsl:apply-templates`
  - `xsl:import`
  - `xsl:include`
  - variables and params
  - `xsl:if`
  - `xsl:choose`
- Deep call-chain tracing in Java.
- Configurable package tracing rules.
- Condition-based branch analysis.
- NetworkX-based local graph creation.
- UI-ready graph output for pipeline and branch visualizations.
- Full structured logging at all layers.
- Trace result conversion helpers such as `to_html()`, `to_graph()`, and `to_neo4j()`.

### 2.2 Excluded from v1

- Database lineage.
- Kafka/Pulsar lineage.
- Runtime execution tracing.
- Live production instrumentation.
- Mandatory Neo4j dependency.
- Real-time continuous sync from Git hosting.

---

## 3. Business Goal

The platform should allow a user to ask:

- Where did this field come from?
- Was it first transformed in XSLT or Java?
- Which methods changed it?
- Which conditions created multiple outcomes?
- What is the final reporting value path?
- Which internal packages were traversed?

The output should help both:

- technical users who want code-level evidence
- business or operations users who want explanation in plain English

---

## 4. Core Assumptions Captured from Discovery

- Tracing is **field by field**.
- The environment is **multi-repo**.
- Build system is **Maven**.
- Java versions may vary from **Java 8 to Java 17+**.
- XSLT usage is heavy and may involve multiple imported stylesheets.
- Enrichment and overriding currently happen in **Java or XSLT**.
- Visual presentation is part of the UI requirement, not a separate optional concern.
- Package tracing must be configurable using patterns such as `*nomura*` or `*no*`.
- A selected field may have one or many possible outcomes, and the UI must show branching clearly.
- Logging is required at all levels.
- Initial implementation priority is:
  1. trace script and parsers
  2. backend API as separate module
  3. frontend UI
- Local graph support should use **Python + NetworkX** first.
- The trace result should support conversion functions for different render/export targets.

---

## 5. High-Level Architecture Phases

### Phase 1 – Trace Core

This phase is the primary focus and must be built first.

Includes:

- repository scanning
- Maven scanning
- Java parsing
- XSLT parsing
- indexing
- cross-linking
- tracing
- branch analysis
- graph building
- graph export
- logging
- explanation generation

### Phase 2 – Backend API

Includes:

- REST endpoints
- orchestration layer
- request validation
- serialization of trace results
- API-level logging

### Phase 3 – Frontend UI

Includes:

- field search
- pipeline visualization
- mind-map / branch visualization
- node details panel
- logs panel
- configuration panel

---

## 6. Functional Requirements

## 6.1 Field-Based Trace Execution

The system must support lineage tracing **one field at a time**.

### Inputs

- `field_name` – mandatory
- `jurisdiction` – optional in v1, but reserved for filtering
- `package_filters` – optional
- `trace_rules` – optional override of default config

### Outputs

For a selected field, the system must return:

- full lineage summary
- origin detection result
- pipeline path
- branch path(s)
- evidence details
- graph payload
- explanation text
- logs/correlation references

---

## 6.2 Origin Detection

The trace engine must determine whether the field appears to be first transformed in:

- XSLT
- Java
- or Java after an XSLT precursor

### Required behavior

1. Scan field-related XSLT mappings and template outputs first.
2. If a field or precursor mapping is found in XSLT, mark origin as `XSLT`.
3. Continue tracing into Java where downstream enrichment, override, or final reporting assignment occurs.
4. If no XSLT origin is found, start from Java.

### Explicit rule

If a field is first derived or transformed in XSLT, the lineage engine must begin from the XSLT template chain and continue through Java until final reporting output is reached.

---

## 6.3 Java Deep Call Chain Tracing

The system must recursively trace method calls across:

- classes
- packages
- modules
- repositories

### Configurable package tracing

The engine must support configurable include/exclude patterns such as:

- `*nomura*`
- `*no*`
- `com.nomura.*`
- exact package names
- optional regex support in future versions

### Required behavior

- If a method call resolves to a class whose package matches configured internal patterns, the trace engine must continue recursively.
- External libraries must be ignored, shallow-traced, or marked as external based on config.
- The engine must preserve the call hierarchy.
- The engine must prevent loops using visited-node tracking.
- The engine must support max depth control.

### Examples of deep trace intent

The system should support flows like:

```java
report.setNCleared(helper.getClearedFlag(trade));
```

and continue into:

```java
helper.getClearedFlag(...)
  -> mapper.resolveStatus(...)
  -> util.normalize(...)
  -> rulesEngine.applyOverride(...)
```

---

## 6.4 XSLT Graph Traversal

The XSLT parser must build a navigable graph, not only flat mappings.

### Must support

- `xsl:template`
- `xsl:call-template`
- `xsl:apply-templates`
- `xsl:import`
- `xsl:include`
- `xsl:variable`
- `xsl:param`
- `xsl:if`
- `xsl:choose`
- output field mappings

### Required behavior

- Resolve template chains.
- Resolve imported and included stylesheets.
- Track variable and parameter propagation.
- Identify where a field is produced, modified, or forwarded.
- Support tracing through multiple XSLT files.

### Example intent

The engine must support tracing logic such as:

```xml
<xsl:call-template name="buildClearingFlag"/>
```

and then continue into the actual template body, its variables, and any nested template/application flow.

---

## 6.5 Condition-Based Analysis

The system must capture and model branch logic affecting a field.

### Must detect

- `if / else`
- `switch`
- ternary operators
- null checks
- default logic
- jurisdiction-specific logic
- config-based flags where statically visible
- XSLT condition structures such as `xsl:if` and `xsl:choose`

### Output requirements

- branch paths
- condition labels
- fallback/default path
- branch-specific evidence

### Example intent

```java
if (trade.isCleared()) {
    report.setNCleared("Y");
} else if ("JP".equals(jurisdiction)) {
    report.setNCleared("N");
} else {
    report.setNCleared(defaultValue);
}
```

The system must return three possible paths, each with its condition.

---

## 6.6 Transformation Classification

Each lineage step must be tagged with a transformation type.

### Required tags

- `EXTRACTION`
- `MAPPING`
- `ENRICHMENT`
- `OVERRIDE`
- `DEFAULTING`
- `PASS_THROUGH`
- `CONDITIONAL_ASSIGNMENT`
- `FINAL_REPORT_ASSIGNMENT`

### Purpose

This classification will support:

- business explanation
- visual styling in UI
- filtering
- graph edge labels

---

## 6.7 Method Output Completeness

The lineage output must include not only that a method was called, but what it effectively contributed.

For every traced Java method, the result must capture:

- inputs used for the field
- field-relevant logic applied inside the method
- conditions affecting the field
- final value returned or assigned by the method
- whether the method enriched, overrode, defaulted, or passed through the field

### Explicit rule

The final output of a method should include everything relevant to the field, not just the existence of the method call.

---

## 6.8 Cross-Linking Between XSLT and Java

The system must bridge XSLT outputs to Java inputs.

### Must support linking through

- DTO population
- mapper classes
- object builders
- report model setters
- helper methods
- intermediate transfer objects where statically inferable

### Goal

Provide one continuous lineage chain from XSLT to Java to final report field.

---

## 6.9 Multi-Repo Maven Support

The scanner must support multiple repositories and Maven structures.

### Must detect

- repository roots
- `pom.xml`
- modules
- inter-module relationships
- source directories
- resources directories
- XSLT locations

### Required behavior

- Resolve intra-repo and cross-repo call chains where source is available.
- Build a package/class/method registry across all scanned repositories.
- Capture Maven module dependencies to help symbol resolution.

---

## 6.10 Evidence Tracking

Every lineage node must carry evidence metadata where available.

### Required evidence fields

- repository
- module
- package
- class or template
- method or template name
- file path
- line number or line range where possible
- transformation type
- condition text if applicable

This evidence must be available in the trace result and UI node details.

---

## 6.11 Graph Generation Using NetworkX

The graph layer must use **Python NetworkX** in v1.

### Graph type

Use `networkx.MultiDiGraph`.

### Why

A field may have multiple relationship types between the same nodes, such as:

- `CALLS`
- `ASSIGNS`
- `OVERRIDES`
- `FLOWS_TO`
- `CONDITION_TRUE`
- `CONDITION_FALSE`

### Graph requirements

- Build a full trace graph for a field.
- Build smaller presentation-ready subgraphs.
- Store metadata on nodes and edges.
- Export graph to UI-ready JSON.

---

## 6.12 Visualization Requirements

Visual output is part of the UI requirement.

### The UI must support

#### Pipeline View

Show the field journey as a step-by-step flow such as:

`Source XML -> XSLT Extraction -> Java Mapper -> Java Enrichment -> Report Builder -> Final Report Field`

#### Branch / Mind-Map View

Where the field has multiple possible outcomes, show branches like:

- condition A -> path A
- condition B -> path B
- fallback -> path C

### UI behavior requirements

- expand/collapse nodes
- zoom/pan support
- condition labels on branches
- transformation-type-aware styling
- clickable nodes for evidence details
- ability to toggle between pipeline and branch view

---

## 6.13 Explanation Layer

The system must provide explanation in two forms.

### Technical explanation

Includes:

- method sequence
- template sequence
- assignment details
- condition paths
- file/class references

### Business explanation

Includes:

- plain-English explanation of how the field is derived
- explanation of alternate outcomes
- explanation of overrides/defaulting in understandable language

---

## 6.14 Configurable Trace Rules

Tracing behavior must be configurable and not hardcoded.

### Configuration must support

- include package patterns
- exclude package patterns
- stop packages
- max recursion depth
- whether to trace external libraries shallowly or ignore them
- whether condition tracing is enabled
- whether XSLT import/include traversal is enabled

### Example config

```yaml
trace:
  includePackages:
    - "*nomura*"
    - "*no*"
  excludePackages:
    - "java.*"
    - "javax.*"
    - "org.springframework.*"
  stopPackages:
    - "org.apache.*"
  maxDepth: 20
  followInternalCallsOnly: true
  enableConditionTracing: true
  enableXsltImports: true
```

---

## 6.15 Logging Requirements

Logging is a first-class requirement.

### Supported log levels

- `TRACE`
- `DEBUG`
- `INFO`
- `WARN`
- `ERROR`

### Logging must exist in

- repo scanning
- Maven parsing
- Java parsing
- XSLT parsing
- cross-linking
- tracing
- condition analysis
- graph building
- export/serialization
- backend API
- explanation layer

### Structured logging fields

Each log entry should include as applicable:

- timestamp
- log level
- module
- message
- trace_id
- field_name
- jurisdiction
- repository
- module_name
- package_name
- class_name
- method_name
- template_name
- recursion_depth
- condition
- exception summary

### Trace correlation

Every trace request must generate a unique `trace_id`, and all logs for that trace must carry the same id.

### Failure transparency

The system must never fail silently.

If trace resolution is partial or incomplete, logs must state:

- unresolved method
- ambiguous symbol match
- unsupported XSLT pattern
- missing field mapping
- max depth reached
- loop prevention triggered
- partial lineage returned

### Log destinations

- console
- rotating file logs
- API-accessible log summary in future UI

### Suggested log files

- `application.log`
- `scanner.log`
- `parser.log`
- `trace.log`
- `audit.log`
- `error.log`

---

## 7. Non-Functional Requirements

### 7.1 Performance

- Pre-index code rather than reparsing everything on every request.
- Cache trace results where useful.
- Support field-specific graph extraction from indexed metadata.

### 7.2 Scalability

- Support multiple repos and multiple Maven modules.
- Handle large codebases incrementally.

### 7.3 Accuracy

- Prefer AST/XML parsing over regex-based inference.
- Preserve evidence for each node to support trust.

### 7.4 Extensibility

- Allow future addition of Python parser hooks.
- Allow future support for Neo4j and database lineage.

### 7.5 Configurability

- Trace behavior, logging level, package rules, and exporters must be configurable.

---

## 8. Project Structure

```text
data-lineage-platform/
│
├── configs/
│   ├── app.yaml
│   ├── trace_rules.yaml
│   ├── logging.yaml
│   └── repositories.yaml
│
├── docs/
│   ├── architecture/
│   ├── tracing/
│   ├── api/
│   └── samples/
│
├── logs/
│   ├── application.log
│   ├── scanner.log
│   ├── parser.log
│   ├── trace.log
│   ├── audit.log
│   └── error.log
│
├── outputs/
│   ├── graphs/
│   ├── json/
│   ├── html/
│   └── debug/
│
├── scripts/
│   ├── run_trace.py
│   ├── run_api.py
│   ├── reindex.py
│   └── sample_trace_request.py
│
├── modules/
│
│   ├── trace_core/
│   │   ├── __init__.py
│   │   │
│   │   ├── scanner/
│   │   │   ├── repo_scanner.py
│   │   │   ├── maven_scanner.py
│   │   │   ├── module_discovery.py
│   │   │   └── file_registry.py
│   │   │
│   │   ├── parsers/
│   │   │   ├── java/
│   │   │   │   ├── java_parser.py
│   │   │   │   ├── ast_extractor.py
│   │   │   │   ├── symbol_resolver.py
│   │   │   │   ├── method_call_extractor.py
│   │   │   │   ├── assignment_extractor.py
│   │   │   │   ├── condition_extractor.py
│   │   │   │   └── return_extractor.py
│   │   │   │
│   │   │   └── xslt/
│   │   │       ├── xslt_parser.py
│   │   │       ├── template_registry.py
│   │   │       ├── import_resolver.py
│   │   │       ├── apply_template_resolver.py
│   │   │       ├── call_template_resolver.py
│   │   │       ├── variable_extractor.py
│   │   │       ├── condition_extractor.py
│   │   │       └── output_mapping_extractor.py
│   │   │
│   │   ├── models/
│   │   │   ├── common.py
│   │   │   ├── java_models.py
│   │   │   ├── xslt_models.py
│   │   │   ├── trace_models.py
│   │   │   └── graph_models.py
│   │   │
│   │   ├── indexers/
│   │   │   ├── repo_indexer.py
│   │   │   ├── java_indexer.py
│   │   │   ├── xslt_indexer.py
│   │   │   ├── dependency_indexer.py
│   │   │   └── cross_link_indexer.py
│   │   │
│   │   ├── tracing/
│   │   │   ├── trace_service.py
│   │   │   ├── field_trace_engine.py
│   │   │   ├── java_trace_engine.py
│   │   │   ├── xslt_trace_engine.py
│   │   │   ├── branch_trace_engine.py
│   │   │   ├── package_filter.py
│   │   │   ├── transformation_classifier.py
│   │   │   ├── trace_context.py
│   │   │   ├── recursion_guard.py
│   │   │   └── evidence_builder.py
│   │   │
│   │   ├── graph/
│   │   │   ├── nx_graph_builder.py
│   │   │   ├── node_factory.py
│   │   │   ├── edge_factory.py
│   │   │   ├── subgraph_builder.py
│   │   │   ├── pipeline_projector.py
│   │   │   ├── branch_projector.py
│   │   │   └── graph_exporter.py
│   │   │
│   │   ├── exporters/
│   │   │   ├── trace_result.py
│   │   │   ├── html_exporter.py
│   │   │   ├── graph_exporter.py
│   │   │   └── neo4j_exporter.py
│   │   │
│   │   ├── explain/
│   │   │   ├── trace_summarizer.py
│   │   │   ├── technical_explainer.py
│   │   │   └── business_explainer.py
│   │   │
│   │   ├── logging/
│   │   │   ├── logger_factory.py
│   │   │   ├── context_logger.py
│   │   │   └── formatters.py
│   │   │
│   │   └── utils/
│   │       ├── file_utils.py
│   │       ├── pattern_utils.py
│   │       ├── collection_utils.py
│   │       └── timer.py
│   │
│   ├── backend_api/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── trace.py
│   │   │   ├── graph.py
│   │   │   ├── config.py
│   │   │   └── logs.py
│   │   ├── schemas/
│   │   │   ├── trace_request.py
│   │   │   ├── trace_response.py
│   │   │   └── graph_response.py
│   │   └── services/
│   │       └── trace_service.py
│   │
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   ├── features/
│       │   │   ├── field-search/
│       │   │   ├── trace-view/
│       │   │   ├── pipeline-view/
│       │   │   ├── branch-view/
│       │   │   ├── node-details/
│       │   │   ├── config-panel/
│       │   │   └── logs-panel/
│       │   └── services/
│       └── public/
│
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 9. Trace Script API Requirements

The trace script must return a trace result object, not only raw dictionaries.

### Core expectation

A field trace invocation should produce:

- structured trace summary
- NetworkX graph object or wrapper
- UI-ready JSON
- export helpers

### Required usage style

The design should support a developer experience similar to:

```python
trace = trace_service.trace(field_name="N_CLEARED")
```

and then allow:

```python
trace.to_graph()
trace.to_html()
trace.to_neo4j()
trace.to_json()
trace.to_pipeline_json()
trace.to_branch_json()
```

### Minimum required exported functions

- `trace()`
- `to_graph()`
- `to_html()`
- `to_neo4j()`
- `to_json()`
- `to_pipeline_json()`
- `to_branch_json()`

### Purpose of each function

#### `trace()`
Runs field lineage resolution and returns a `TraceResult` object.

#### `to_graph()`
Returns the underlying NetworkX graph or an export-safe wrapper.

#### `to_html()`
Returns an HTML representation of the trace for local preview or reporting.

#### `to_neo4j()`
Returns a Neo4j-compatible export payload, even if Neo4j is not used immediately in v1.

#### `to_json()`
Returns the canonical serialized trace result.

#### `to_pipeline_json()`
Returns data optimized for pipeline visualization.

#### `to_branch_json()`
Returns data optimized for branch/mind-map visualization.

---

## 10. Sample Trace Script Usage

### Example 1 – Basic trace

```python
from modules.trace_core.tracing.trace_service import TraceService

service = TraceService()
trace = service.trace(field_name="N_CLEARED")

print(trace.summary)
```

### Example 2 – Convert to graph

```python
graph = trace.to_graph()
print(graph.nodes(data=True))
print(graph.edges(data=True))
```

### Example 3 – Export to HTML

```python
html = trace.to_html()
with open("outputs/html/n_cleared_trace.html", "w", encoding="utf-8") as f:
    f.write(html)
```

### Example 4 – Export to JSON

```python
payload = trace.to_json()
```

### Example 5 – Pipeline-specific payload

```python
pipeline_payload = trace.to_pipeline_json()
```

### Example 6 – Branch-specific payload

```python
branch_payload = trace.to_branch_json()
```

### Example 7 – Neo4j-compatible export

```python
neo4j_payload = trace.to_neo4j()
```

---

## 11. Sample TraceResult Interface

The project should include a trace result abstraction that exposes graph and export helpers.

### Illustrative interface

```python
class TraceResult:
    def __init__(self, field_name, summary, graph, metadata, evidence, branches):
        self.field_name = field_name
        self.summary = summary
        self.graph = graph
        self.metadata = metadata
        self.evidence = evidence
        self.branches = branches

    def to_graph(self):
        return self.graph

    def to_json(self):
        ...

    def to_pipeline_json(self):
        ...

    def to_branch_json(self):
        ...

    def to_html(self):
        ...

    def to_neo4j(self):
        ...
```

### Note

The exact implementation may differ, but the trace result must behave like a reusable result object rather than a one-off script dump.

---

## 12. Sample Trace Scenarios That Must Be Supported

These examples reflect the kinds of trace behavior discussed during requirement discovery.

### Scenario 1 – XSLT extraction followed by Java enrichment

Expected support:

1. field originates in XSLT
2. field is passed into Java mapping layer
3. field is enriched in Java helper/service class
4. field is assigned into final reporting object
5. output includes pipeline + evidence + explanation

### Scenario 2 – Java deep internal call chain

Expected support:

A field assignment like:

```java
report.setNCleared(helper.getClearedFlag(trade));
```

must trace through all matching internal packages and capture:

- call hierarchy
- conditions
- returned values
- final assignment

### Scenario 3 – Branching based on condition

Expected support:

```java
if (trade.isCleared()) {
    report.setNCleared("Y");
} else if ("JP".equals(jurisdiction)) {
    report.setNCleared("N");
} else {
    report.setNCleared(defaultValue);
}
```

The trace output must show three branches in the branch graph.

### Scenario 4 – Heavy XSLT template chain

Expected support:

- template A calls template B
- template B applies templates from imported stylesheet C
- variable values are propagated across templates
- final field output is linked into Java processing

### Scenario 5 – Package-filtered deep traversal

Expected support:

When configured with `*nomura*`, the engine must deeply trace matching internal packages while avoiding irrelevant external code.

---

## 13. Backend API Requirements

The backend must be a separate module from trace core.

### It must expose endpoints such as

- `POST /trace/field`
- `GET /graph/field/{field_name}`
- `GET /config`
- `GET /logs/{trace_id}`

### The backend must

- call the trace core as a library
- return serialized trace results
- expose pipeline and branch payloads
- preserve `trace_id`
- log request/response flow

---

## 14. Frontend Requirements

The frontend must be built after the trace output structure stabilizes.

### Must include

- field search view
- trace execution action
- pipeline visualization panel
- mind-map / branch panel
- node details drawer
- config/filter panel
- logs panel

### Visual requirements

- pipeline must show the field journey from origin to final output
- branches must show alternate outcomes with conditions
- node click should show repo, file, line, method/template, and explanation

---

## 15. Implementation Sequence

### Step 1

Focus on the **trace script and parsers**.

This includes:

- scanner
- parsers
- indexers
- tracing
- graph generation
- exporters
- logging

### Step 2

Build **backend API** as a separate module.

### Step 3

Build **frontend**.

---

## 16. Summary

This platform is not only a code scanner and not only a visualization utility.

It is intended to become a **field-level logic derivation engine** that can:

- understand where a field came from
- show how it moved through XSLT and Java
- explain why it changed
- visualize all possible outcomes
- export its result for local graph, HTML, JSON, and future Neo4j usage

