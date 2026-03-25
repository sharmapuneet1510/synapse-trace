# Synapse Trace -- API Documentation

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## Table of Contents

1. [Health](#health)
2. [Jurisdictions](#jurisdictions)
3. [Fields](#fields)
4. [XPath Lookup](#xpath-lookup)
5. [Translation](#translation)
6. [Parse](#parse)
7. [Dashboard](#dashboard)
8. [Chat](#chat)
9. [LLM](#llm)
10. [Using the Orchestrator Directly](#using-the-orchestrator-directly)
11. [Configuration via jurisdiction.json](#configuration-via-jurisdictionjson)
12. [Connecting Your Own LLM](#connecting-your-own-llm)
13. [Database: Switching from SQLite to MSSQL](#database-switching-from-sqlite-to-mssql)

---

## Health

### GET /api/health

Returns service health status.

**Response:**

```json
{
  "status": "ok",
  "service": "synapse-trace"
}
```

---

## Jurisdictions

### GET /api/jurisdictions

List all configured jurisdictions.

**Response:** `JurisdictionSummary[]`

```json
[
  {
    "id": "hkma",
    "name": "HKMA",
    "display_name": "Hong Kong Monetary Authority",
    "module_type": "dtcc/iso",
    "config_types": ["TradeState", "Valuation"],
    "field_count": 26
  },
  {
    "id": "mas",
    "name": "MAS",
    "display_name": "Monetary Authority of Singapore",
    "module_type": "exception-service",
    "config_types": ["TradeState", "Valuation"],
    "field_count": 7
  }
]
```

### GET /api/jurisdictions/{jurisdiction_id}

Get full details for a single jurisdiction, including all config types and field definitions.

**Path Parameters:**

| Parameter        | Type   | Description         |
|------------------|--------|---------------------|
| jurisdiction_id  | string | e.g. `hkma`, `mas`  |

**Response:** `JurisdictionConfig`

```json
{
  "id": "hkma",
  "name": "HKMA",
  "display_name": "Hong Kong Monetary Authority",
  "git_path": "/repos/hkma-reporting",
  "lib_path": "/repos/hkma-common-lib",
  "absolute_download_path": "/data/downloads/hkma",
  "module_type": "dtcc/iso",
  "configs": {
    "TradeState": {
      "fields": [
        {
          "header": "Effective Date",
          "field_name": "N_EFFECTIVE_DATE",
          "asset_classes": ["InterestRate", "CDS", "FX"]
        }
      ]
    },
    "Valuation": {
      "fields": [
        {
          "header": "Mark to Market Value",
          "field_name": "N_MTM_VALUE",
          "asset_classes": ["InterestRate", "CDS"]
        }
      ]
    }
  }
}
```

**Errors:**
- `404`: Jurisdiction not found

### GET /api/jurisdictions/{jurisdiction_id}/configs/{config_type}

Get fields for a specific config type within a jurisdiction.

**Path Parameters:**

| Parameter        | Type   | Description                        |
|------------------|--------|------------------------------------|
| jurisdiction_id  | string | e.g. `hkma`                       |
| config_type      | string | e.g. `TradeState` or `Valuation`   |

**Response:** `ConfigTypeResponse`

```json
{
  "config_type": "TradeState",
  "jurisdiction_id": "hkma",
  "fields": [
    {
      "header": "Effective Date",
      "field_name": "N_EFFECTIVE_DATE",
      "asset_classes": ["InterestRate", "CDS", "FX"]
    },
    {
      "header": "Trade ID",
      "field_name": "N_TRADE_ID",
      "asset_classes": ["InterestRate", "CDS", "FX"]
    }
  ]
}
```

**Errors:**
- `404`: Config type not found

---

## Fields

### GET /api/fields/{jurisdiction_id}/{field_name}

Get comprehensive field detail including XSLT logic, XPath entries, Java references, and lineage dependencies.

**Path Parameters:**

| Parameter        | Type   | Description                      |
|------------------|--------|----------------------------------|
| jurisdiction_id  | string | e.g. `hkma`                     |
| field_name       | string | e.g. `N_EFFECTIVE_DATE`          |

**Response:** `FieldDetail`

```json
{
  "jurisdiction_id": "hkma",
  "field_name": "N_EFFECTIVE_DATE",
  "header": "Effective Date",
  "asset_classes": ["InterestRate", "CDS", "FX"],
  "config_type": "TradeState",
  "xslt_logic": "<xsl:value-of select=\"order/effectiveDate\"/>",
  "xslt_file": "/repos/hkma-reporting/src/main/resources/xslt/trade.xsl",
  "xslt_line": 42,
  "input_xpaths": [
    {
      "name": "effectiveDate",
      "source": "trade.xsl",
      "xpath": "order/effectiveDate",
      "template": "TradeStateTemplate",
      "output_element": "EffectiveDate",
      "line": 42
    }
  ],
  "dependencies": [
    {
      "field_name": "N_EXPIRATION_DATE",
      "relationship": "DERIVED_FROM",
      "source_type": "java",
      "file_path": "/repos/hkma-reporting/src/main/java/TradeMapper.java",
      "line_number": 85
    }
  ],
  "java_references": [
    {
      "class_name": "com.bank.TradeMapper",
      "method_name": "mapFields",
      "finding_type": "constant_ref",
      "code_snippet": "map.put(MessageKey.N_EFFECTIVE_DATE, trade.getEffectiveDate())",
      "file_path": "/repos/hkma-reporting/src/main/java/TradeMapper.java",
      "line_number": 85
    }
  ]
}
```

**Notes:** The `xslt_logic`, `input_xpaths`, `dependencies`, and `java_references` fields are populated only after a parse has been triggered and completed for the jurisdiction. Before parsing, only the static config fields (`header`, `field_name`, `asset_classes`, `config_type`) are returned.

**Errors:**
- `404`: Field not found in the given jurisdiction

---

## XPath Lookup

### POST /api/xpath/lookup

Reverse lookup: find all XSLT XPath expressions that reference a given field name. Searches across the XPath index built during parsing.

**Request Body:** `XPathLookupRequest`

| Field            | Type            | Required | Description                                  |
|------------------|-----------------|----------|----------------------------------------------|
| field_name       | string          | yes      | Field name to look up (e.g. `N_EFFECTIVE_DATE`) |
| jurisdiction_id  | string or null  | no       | Limit search to a specific jurisdiction. If null, searches all. |

**Example Request:**

```json
{
  "field_name": "N_EFFECTIVE_DATE",
  "jurisdiction_id": "hkma"
}
```

**Response:** `XPathLookupResponse`

```json
{
  "field_name": "N_EFFECTIVE_DATE",
  "matches": [
    {
      "name": "effectiveDate",
      "source": "trade.xsl",
      "xpath": "order/effectiveDate",
      "template": "TradeStateTemplate",
      "output_element": "EffectiveDate",
      "line": 42
    }
  ],
  "total": 1
}
```

**Notes:** Requires a completed parse. Uses canonical key matching, so `N_EFFECTIVE_DATE` will match XPaths containing `effectiveDate`, `EFFECTIVE_DATE`, etc.

---

## Translation

### POST /api/translation/explain

Translate a field's code logic into business terms. Currently returns placeholder content (stub). Will produce LLM-generated content once an LLM is connected.

**Request Body:** `TranslationRequest`

| Field            | Type            | Required | Description                          |
|------------------|-----------------|----------|--------------------------------------|
| field_name       | string          | yes      | Field name                           |
| jurisdiction_id  | string          | yes      | Jurisdiction ID                      |
| code_snippet     | string or null  | no       | Code snippet for context             |
| xpaths           | string[] or null| no       | Related XPath expressions            |
| dependencies     | string[] or null| no       | Related dependency field names       |

**Example Request:**

```json
{
  "field_name": "N_EFFECTIVE_DATE",
  "jurisdiction_id": "hkma",
  "code_snippet": "trade.setEffectiveDate(source.getEffectiveDate())",
  "xpaths": ["order/effectiveDate"],
  "dependencies": ["N_EXPIRATION_DATE"]
}
```

**Response:** `TranslationResult`

```json
{
  "field_name": "N_EFFECTIVE_DATE",
  "business_derivation": "BUSINESS PURPOSE: N_EFFECTIVE_DATE is a critical field for HKMA regulatory reporting...",
  "reporting_logic": "Step 1: Check if N_EFFECTIVE_DATE value exists in the source trade data...",
  "internal_enrichment": "DTCC XML Based -> (DataPath)/Documents/SortByProductType/...",
  "downstream_mapping": "The N_EFFECTIVE_DATE field is consumed by the following downstream systems...",
  "examples": [
    "EXAMPLE 1: Interest Rate IRS -- A 5-year IRS traded on March 1st...",
    "EXAMPLE 2: Credit Default Swap -- ...",
    "EXAMPLE 3: Bermuda Bond Option -- ...",
    "EXAMPLE 4: FX Forward -- ...",
    "EXAMPLE 5: Equity Swap -- ..."
  ],
  "operational_guidance": "WORKING SCENARIO 1: Maturity Processing -- Operations team runs..."
}
```

---

## Parse

### POST /api/parse/trigger

Trigger a batch parse of all jurisdictions. Runs asynchronously in a background thread. For each jurisdiction, the system scans the `git_path` and `lib_path`, parses Java and XSLT files, stitches findings, and caches the results.

**Request Body:** None

**Response:**

```json
{
  "status": "started",
  "message": "Parsing 3 jurisdictions"
}
```

Or if a parse is already running:

```json
{
  "status": "already_running",
  "message": "Batch parse is already in progress"
}
```

### GET /api/parse/status

Get the current parse status for all jurisdictions.

**Response:**

```json
{
  "batch_status": "done",
  "batch_started": "2025-03-15T10:30:00",
  "batch_completed": "2025-03-15T10:30:45",
  "jurisdictions": {
    "hkma": {
      "status": "ready",
      "parsed_at": "2025-03-15T10:30:15",
      "java_findings": 245,
      "xslt_findings": 89,
      "nodes": 120,
      "edges": 95,
      "error": null
    },
    "mas": {
      "status": "ready",
      "parsed_at": "2025-03-15T10:30:30",
      "java_findings": 180,
      "xslt_findings": 45,
      "nodes": 80,
      "edges": 60,
      "error": null
    }
  }
}
```

**Status values:** `idle`, `running`, `done`, `error` (batch); `pending`, `parsing`, `ready`, `error` (jurisdiction)

### GET /api/parse/logs

Get recent parse log entries.

**Query Parameters:**

| Parameter | Type | Default | Description              |
|-----------|------|---------|--------------------------|
| limit     | int  | 100     | Max number of log entries |

**Response:** `LogEntry[]`

```json
[
  {
    "timestamp": "2025-03-15T10:30:00.123456",
    "level": "info",
    "message": "Batch parse started",
    "jurisdiction_id": null
  },
  {
    "timestamp": "2025-03-15T10:30:01.234567",
    "level": "info",
    "message": "Starting parse for HKMA",
    "jurisdiction_id": "hkma"
  }
]
```

---

## Dashboard

### GET /api/dashboard/stats

Get aggregate statistics across all jurisdictions.

**Response:**

```json
{
  "batch_status": "done",
  "batch_started": "2025-03-15T10:30:00",
  "batch_completed": "2025-03-15T10:30:45",
  "totals": {
    "java_findings": 500,
    "xslt_findings": 200,
    "nodes": 300,
    "edges": 250
  },
  "jurisdictions": [
    {
      "id": "hkma",
      "status": "ready",
      "java_findings": 245,
      "xslt_findings": 89,
      "nodes": 120,
      "edges": 95,
      "parsed_at": "2025-03-15T10:30:15"
    }
  ]
}
```

### GET /api/dashboard/nodes/{jurisdiction_id}

Get lineage graph nodes for a jurisdiction (paginated).

**Path Parameters:**

| Parameter        | Type   | Description  |
|------------------|--------|--------------|
| jurisdiction_id  | string | e.g. `hkma`  |

**Query Parameters:**

| Parameter | Type | Default | Description       |
|-----------|------|---------|-------------------|
| limit     | int  | 100     | Page size          |
| offset    | int  | 0       | Starting position  |

**Response:**

```json
{
  "nodes": [
    {
      "id": "java::class::com.bank.TradeMapper",
      "label": "TradeMapper",
      "type": "java_class",
      "file_path": "/repos/hkma-reporting/src/main/java/TradeMapper.java",
      "line_number": 15,
      "code_snippet": "public class TradeMapper {"
    }
  ],
  "total": 120
}
```

### GET /api/dashboard/edges/{jurisdiction_id}

Get lineage graph edges for a jurisdiction (paginated).

**Path Parameters:**

| Parameter        | Type   | Description  |
|------------------|--------|--------------|
| jurisdiction_id  | string | e.g. `hkma`  |

**Query Parameters:**

| Parameter | Type | Default | Description       |
|-----------|------|---------|-------------------|
| limit     | int  | 100     | Page size          |
| offset    | int  | 0       | Starting position  |

**Response:**

```json
{
  "edges": [
    {
      "source": "java::class::com.bank.TradeMapper",
      "target": "java::method::com.bank.TradeMapper::mapFields",
      "type": "CALLS"
    }
  ],
  "total": 95
}
```

**Edge types:** `CALLS`, `DERIVED_FROM`, `TRANSFORMS`, `LOADS_XSLT`, `CROSS_REPO`, `UNMARSHALS_TO`

### GET /api/dashboard/live

Server-Sent Events (SSE) endpoint for live parse logs. Returns a streaming response with heartbeats every second.

**Response:** `text/event-stream`

```
data: {"timestamp":"2025-03-15T10:30:00","level":"info","message":"Starting parse...","jurisdiction_id":"hkma"}

data: {"type":"heartbeat","batch_status":"running","timestamp":"2025-03-15T10:30:01"}

data: {"timestamp":"2025-03-15T10:30:02","level":"info","message":"Parsed TradeMapper.java: 15 findings","jurisdiction_id":"hkma"}
```

---

## Chat

### POST /api/chat/sessions

Create a new chat session.

**Request Body:** `ChatSessionCreate` (optional, can be empty)

| Field    | Type           | Default     | Description          |
|----------|----------------|-------------|----------------------|
| title    | string or null | null        | Session title        |
| user_id  | string         | `"default"` | User identifier      |

**Example Request:**

```json
{
  "title": "HKMA field questions",
  "user_id": "analyst_1"
}
```

**Response:** `ChatSessionResponse`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "HKMA field questions",
  "created_at": "2025-03-15T10:30:00Z",
  "updated_at": "2025-03-15T10:30:00Z",
  "message_count": 0
}
```

### GET /api/chat/sessions

List chat sessions for a user.

**Query Parameters:**

| Parameter | Type   | Default     | Description              |
|-----------|--------|-------------|--------------------------|
| user_id   | string | `"default"` | User identifier          |
| limit     | int    | 50          | Max sessions to return   |

**Response:** `ChatSessionResponse[]`

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "HKMA field questions",
    "created_at": "2025-03-15T10:30:00Z",
    "updated_at": "2025-03-15T11:00:00Z",
    "message_count": 4
  }
]
```

### GET /api/chat/sessions/{session_id}

Get a chat session with all messages.

**Path Parameters:**

| Parameter  | Type   | Description |
|------------|--------|-------------|
| session_id | string | Session UUID |

**Response:** `ChatSessionDetail`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "HKMA field questions",
  "created_at": "2025-03-15T10:30:00Z",
  "updated_at": "2025-03-15T11:00:00Z",
  "message_count": 2,
  "messages": [
    {
      "id": "msg-uuid-1",
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "role": "user",
      "content": "What does N_EFFECTIVE_DATE mean?",
      "jurisdiction_id": "hkma",
      "field_name": "N_EFFECTIVE_DATE",
      "created_at": "2025-03-15T10:31:00Z"
    },
    {
      "id": "msg-uuid-2",
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "role": "assistant",
      "content": "[Stub Response] (jurisdiction: HKMA, field: N_EFFECTIVE_DATE)...",
      "jurisdiction_id": "hkma",
      "field_name": "N_EFFECTIVE_DATE",
      "created_at": "2025-03-15T10:31:01Z"
    }
  ]
}
```

**Errors:**
- `404`: Session not found

### POST /api/chat/sessions/{session_id}/messages

Send a message to a chat session. The system persists the user message, generates an LLM response (currently a stub), persists the assistant message, and returns both.

**Path Parameters:**

| Parameter  | Type   | Description |
|------------|--------|-------------|
| session_id | string | Session UUID |

**Request Body:** `ChatMessageCreate`

| Field            | Type           | Required | Description                          |
|------------------|----------------|----------|--------------------------------------|
| content          | string         | yes      | Message text                         |
| jurisdiction_id  | string or null | no       | Context: which jurisdiction          |
| field_name       | string or null | no       | Context: which field                 |

**Example Request:**

```json
{
  "content": "What does N_EFFECTIVE_DATE mean in HKMA reporting?",
  "jurisdiction_id": "hkma",
  "field_name": "N_EFFECTIVE_DATE"
}
```

**Response:** `ChatMessageResponse[]` (always returns 2 messages: user + assistant)

```json
[
  {
    "id": "msg-uuid-1",
    "session_id": "a1b2c3d4-...",
    "role": "user",
    "content": "What does N_EFFECTIVE_DATE mean in HKMA reporting?",
    "jurisdiction_id": "hkma",
    "field_name": "N_EFFECTIVE_DATE",
    "created_at": "2025-03-15T10:31:00Z"
  },
  {
    "id": "msg-uuid-2",
    "session_id": "a1b2c3d4-...",
    "role": "assistant",
    "content": "[Stub Response] (jurisdiction: HKMA, field: N_EFFECTIVE_DATE)...",
    "jurisdiction_id": "hkma",
    "field_name": "N_EFFECTIVE_DATE",
    "created_at": "2025-03-15T10:31:01Z"
  }
]
```

**Errors:**
- `404`: Session not found

### DELETE /api/chat/sessions/{session_id}

Delete a chat session and all its messages.

**Path Parameters:**

| Parameter  | Type   | Description |
|------------|--------|-------------|
| session_id | string | Session UUID |

**Response:**

```json
{
  "status": "deleted",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Errors:**
- `404`: Session not found

---

## LLM

### POST /api/llm/describe

Generate a business description for a field. Currently returns a stub response.

**Request Body:** `DescribeRequest`

| Field            | Type            | Required | Description                    |
|------------------|-----------------|----------|--------------------------------|
| field_name       | string          | yes      | Field name                     |
| jurisdiction_id  | string          | yes      | Jurisdiction ID                |
| code_logic       | string or null  | no       | Code logic for context         |
| xpaths           | string[] or null| no       | Related XPath expressions      |

**Example Request:**

```json
{
  "field_name": "N_EFFECTIVE_DATE",
  "jurisdiction_id": "hkma",
  "code_logic": "trade.getEffectiveDate()",
  "xpaths": ["order/effectiveDate"]
}
```

**Response:** `DescribeResponse`

```json
{
  "field_name": "N_EFFECTIVE_DATE",
  "jurisdiction_id": "hkma",
  "description": "The field N_EFFECTIVE_DATE serves as a key data point in HKMA regulatory submissions. It captures essential trade information required for compliance reporting under the jurisdiction's regulatory framework.\n\nBusiness Impact: This field directly affects the accuracy of regulatory submissions and must be populated correctly to avoid reporting discrepancies."
}
```

---

## Using the Orchestrator Directly

The orchestrator layer (`src/orchestrator/`) can be used independently of the API for programmatic lineage tracing.

### JavaParser

```python
from orchestrator.parsers.java_parser import JavaParser
from pathlib import Path

parser = JavaParser(repo_name="my-app")
findings = parser.parse_file(Path("src/main/java/TradeMapper.java"))
# findings: list[JavaFinding]
# Each finding has: class_name, method_name, field_name, finding_type,
#                    target_class, target_field, meta, repo_name

# Parse an entire directory
all_findings = parser.parse_directory(Path("src/main/java"))
```

Finding types: `method_call`, `unmarshal`, `field_mapping`, `constant_ref`, `string_literal`, `xslt_ref`

### XsltParser

```python
from orchestrator.parsers.xslt_parser import XsltParser
from pathlib import Path

parser = XsltParser(repo_name="my-app")
findings = parser.parse_file(Path("src/main/resources/xslt/trade.xsl"))
# findings: list[XsltFinding]
# Each finding has: template_name, template_match, field_source, field_target,
#                    finding_type, meta, repo_name

# Parse an entire directory
all_findings = parser.parse_directory(Path("src/main/resources/xslt"))
```

Finding types: `value_of`, `template_call`, `field_mapping`

### ModuleScanner

```python
from orchestrator.scanner import ModuleScanner
from pathlib import Path

scanner = ModuleScanner()

# Scan a single module
module = scanner.scan(Path("src/"), name="my-module")
# module.java_files, module.xslt_files, module.xslt_refs

# Scan a multi-module project (auto-discovers sub-modules)
project = scanner.scan_project(Path("/repos/my-project"), name="my-project")
# project.modules: list[ScannedModule]
# project.total_java, project.total_xslt, project.total_refs
```

### Stitcher

```python
from orchestrator.stitcher import Stitcher

stitcher = Stitcher()
lineage = stitcher.stitch(java_findings, xslt_findings)
# lineage.nodes: list[LineageNode]
# lineage.edges: list[LineageEdge]
```

### quick_trace (Recommended High-Level API)

```python
from orchestrator.quick_trace import trace_project

# Trace a project with library dependencies
result = trace_project(
    main="/code/my-app",
    libs=["/code/lib-fields", "/code/lib-common"],
)

result.print_summary()    # Nodes, edges, findings summary
result.print_nodes()      # All nodes
result.print_edges()      # All edges

# Export options
result.to_json("output/lineage.json")       # Node-link JSON
result.to_html("output/lineage.html")       # PyVis interactive HTML
result.to_cypher("output/lineage.cypher")   # Neo4j Cypher statements
result.to_neo4j_json("output/neo4j.json")   # APOC-compatible JSON

# Push directly to Neo4j
result.to_neo4j(uri="bolt://localhost:7687", user="neo4j", password="secret")

# Trace only specific fields
result = trace_project(
    main="/code/my-app",
    targets=["N_EFFECTIVE_DATE", "N_TRADE_ID"],
)

# Or filter after the fact
full = trace_project(main="/code/my-app", libs=[...])
subset = full.filter("N_EFFECTIVE_DATE")
subset.print_summary()
```

### Registering Custom Parsers

```python
from orchestrator.quick_trace import register_parser

class MyGroovyParser:
    def __init__(self, repo_name: str = "") -> None:
        self._repo_name = repo_name

    def parse_file(self, file_path):
        # Return list of JavaFinding or XsltFinding objects
        ...

register_parser(".groovy", MyGroovyParser)
# Now .groovy files will be parsed automatically during scanning
```

---

## Configuration via jurisdiction.json

The file `jurisdiction.json` at the project root defines all jurisdictions. Structure:

```json
{
  "jurisdictions": [
    {
      "id": "hkma",
      "name": "HKMA",
      "display_name": "Hong Kong Monetary Authority",
      "git_path": "/repos/hkma-reporting",
      "lib_path": "/repos/hkma-common-lib",
      "absolute_download_path": "/data/downloads/hkma",
      "module_type": "dtcc/iso",
      "configs": {
        "TradeState": {
          "fields": [
            {
              "header": "Effective Date",
              "field_name": "N_EFFECTIVE_DATE",
              "asset_classes": ["InterestRate", "CDS", "FX"]
            }
          ]
        },
        "Valuation": {
          "fields": [
            {
              "header": "Mark to Market Value",
              "field_name": "N_MTM_VALUE",
              "asset_classes": ["InterestRate", "CDS"]
            }
          ]
        }
      }
    }
  ]
}
```

**Field reference:**

| Field                  | Type   | Description                                             |
|------------------------|--------|---------------------------------------------------------|
| id                     | string | Unique short identifier (used in API paths)             |
| name                   | string | Short display name                                      |
| display_name           | string | Full human-readable name                                |
| git_path               | string | Path to the main code repository                        |
| lib_path               | string | Path to the shared library repository                   |
| absolute_download_path | string | Path for downloaded artifacts                           |
| module_type            | string | Module classification: `dtcc/iso`, `exception-service`  |
| configs                | object | Map of config type name to field list                   |
| configs.*.fields       | array  | Array of field definitions                              |
| fields[].header        | string | Business-facing field name                              |
| fields[].field_name    | string | Code-level variable name (e.g., `N_EFFECTIVE_DATE`)     |
| fields[].asset_classes | array  | Asset classes this field applies to                     |

The file is loaded at API startup via `jurisdiction_service.load_config()`. Adding a new jurisdiction only requires adding an entry to this file and restarting the server.

---

## Connecting Your Own LLM

The LLM service at `src/api/services/llm_service.py` uses a stub pattern. To connect a real LLM:

1. Edit the `_call_llm` method in `LLMService`:

```python
async def _call_llm(self, prompt: str, context: dict | None = None) -> str:
    # OpenAI example:
    import openai
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

    # Azure OpenAI example:
    # from openai import AzureOpenAI
    # client = AzureOpenAI(endpoint=..., api_key=..., api_version=...)
    # response = client.chat.completions.create(...)
    # return response.choices[0].message.content
```

2. Update `generate_business_description` and `answer_chat_query` to call `await self._call_llm(prompt)` instead of returning hardcoded strings.

The stub responses currently have the format `"[LLM Stub Response] ..."` and `"[Stub Response] ..."` to make it clear they are placeholders.

---

## Database: Switching from SQLite to MSSQL

The database layer is in `src/api/database.py`. Currently configured for SQLite:

```python
DATABASE_URL = "sqlite:///./synapse_trace.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

To switch to Microsoft SQL Server:

1. Install the MSSQL driver:
   ```bash
   pip install pyodbc
   ```

2. Update `database.py`:
   ```python
   DATABASE_URL = "mssql+pyodbc://username:password@hostname/dbname?driver=ODBC+Driver+17+for+SQL+Server"
   engine = create_engine(DATABASE_URL)
   ```

3. Remove the `connect_args={"check_same_thread": False}` parameter (SQLite-specific).

The ORM models (`ChatSession`, `ChatMessage`) use standard SQLAlchemy types (`String`, `Text`, `DateTime`) that are compatible with both SQLite and MSSQL without modification. The `init_db()` function calls `Base.metadata.create_all()` which will auto-create tables on startup.
