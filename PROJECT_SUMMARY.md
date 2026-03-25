# Synapse Trace -- Project Summary

## Overview

**Synapse Trace** is a data lineage tracer for regulatory reporting systems. It parses Java and XSLT codebases used in financial trade reporting, stitches cross-language references into a unified lineage graph, and serves the results through a FastAPI backend to a React TypeScript frontend. The system helps teams understand how trade data fields flow from source systems through transformation layers to regulatory submissions (e.g., HKMA, MAS, DTCC).

---

## Tech Stack

| Layer          | Technology                                                    |
|----------------|---------------------------------------------------------------|
| Backend API    | Python 3.10+, FastAPI, Uvicorn                                |
| Database       | SQLAlchemy ORM, SQLite (swappable to MSSQL)                   |
| Orchestrator   | Custom Python parsers (regex-based Java, lxml-based XSLT)     |
| Graph Storage  | PyVis (HTML), Neo4j (optional)                                |
| Frontend       | React 18, TypeScript, Vite                                    |
| State Mgmt     | Zustand (client state), React Query / TanStack Query (server) |
| Styling        | CSS (component-level)                                         |

---

## Architecture Overview

```
jurisdiction.json
       |
       v
+------------------+     +--------------------+     +------------------+
|  Orchestrator     |     |   FastAPI Backend   |     |  React Frontend  |
|                   |     |                     |     |                  |
|  ModuleScanner    |---->|  ParseCache         |---->|  Zustand Store   |
|  JavaParser       |     |  JurisdictionSvc    |     |  React Query     |
|  XsltParser       |     |  FieldService       |     |  AppShell        |
|  Stitcher         |     |  XPathIndex         |     |  (Header/Sidebar |
|  quick_trace      |     |  LLM Service (stub) |     |   /Main)         |
+------------------+     |  Chat Service       |     +------------------+
                          +--------------------+
```

---

## Directory Structure

```
synapse-trace/
  jurisdiction.json              # Jurisdiction configuration (HKMA, MAS, DTCC)
  pyproject.toml                 # Python project metadata
  requirements.txt               # Python dependencies

  src/
    api/                         # FastAPI application
      main.py                    # App factory, lifespan, CORS, router registration
      config.py                  # Paths (BASE_DIR, JURISDICTION_JSON), CORS origins
      database.py                # SQLAlchemy engine, SessionLocal, Base, init_db()
      models/
        chat.py                  # ChatSession and ChatMessage ORM models
      routers/
        jurisdictions.py         # GET /api/jurisdictions, /{id}, /{id}/configs/{type}
        fields.py                # GET /api/fields/{jurisdiction_id}/{field_name}
        xpath.py                 # POST /api/xpath/lookup
        translation.py           # POST /api/translation/explain
        parse.py                 # POST /api/parse/trigger, GET /status, GET /logs
        dashboard.py             # GET /api/dashboard/stats, /nodes, /edges, /live (SSE)
        chat.py                  # CRUD for chat sessions and messages
        llm.py                   # POST /api/llm/describe
      schemas/
        jurisdiction.py          # FieldConfig, ConfigType, JurisdictionConfig, etc.
        field.py                 # FieldDetail, XPathEntry, DependencyRef, JavaReference
        translation.py           # TranslationRequest, TranslationResult
        xpath.py                 # XPathLookupRequest, XPathLookupResponse
        chat.py                  # ChatMessageCreate/Response, ChatSessionCreate/Detail
      services/
        jurisdiction_service.py  # Loads/validates jurisdiction.json, get_all/get_by_id
        field_service.py         # Assembles FieldDetail from cache + jurisdiction config
        cache.py                 # ParseCache singleton (in-memory, thread-safe)
        parse_service.py         # Batch parse: scan -> parse -> stitch -> cache
        xpath_service.py         # XPathIndex reverse lookup (field_name -> XPath entries)
        translation_service.py   # Stub: generates placeholder business translations
        llm_service.py           # Stub LLM service (_call_llm placeholder)
        chat_service.py          # CRUD for ChatSession/ChatMessage via SQLAlchemy

    orchestrator/                # Core lineage engine (standalone, no FastAPI dependency)
      parser.py                  # SynapseTracer CLI orchestrator (--project, --scan, --config)
      scanner.py                 # ModuleScanner: discovers .java/.xslt files, detects refs
      stitcher.py                # Stitcher: cross-language field matching, graph building
      quick_trace.py             # Functional API: trace_project(), TraceResult, filter()
      live_events.py             # Event emitter for real-time scan/parse/stitch progress
      models.py                  # JavaFinding, XsltFinding, LineageNode/Edge, NodeType, etc.
      parsers/
        java_parser.py           # Regex-based Java parser (methods, fields, constants, XSLT refs)
        xslt_parser.py           # lxml-based XSLT parser (templates, value-of, call-template)
      storage/
        base_provider.py         # Abstract BaseGraphProvider interface
        local_graph_pyvis.py     # PyVis HTML graph output
        neo4j_adapter.py         # Neo4j Cypher generation and driver adapter

  frontend/
    src/
      main.tsx                   # React entry point
      App.tsx                    # Root component
      api/
        client.ts                # Base HTTP client (fetch wrapper with /api prefix)
        jurisdictions.ts         # fetchJurisdictions, fetchConfigType
        fields.ts                # fetchFieldDetail
        translation.ts           # fetchTranslation
        dashboard.ts             # fetchDashboardStats, fetchNodes, fetchEdges
        chat.ts                  # Chat session/message API calls
        llm.ts                   # describeFIeld API call
      hooks/
        useJurisdictions.ts      # useQuery for jurisdictions and config types
        useFieldDetail.ts        # useQuery for field detail
        useTranslation.ts        # useMutation for translation explain
        useDashboard.ts          # useQuery for dashboard stats, nodes, edges
        useChat.ts               # useQuery/useMutation for chat CRUD
        useLLM.ts                # useMutation for LLM describe
      stores/
        appStore.ts              # Zustand store: jurisdictionId, configType, fieldName, etc.
      types/
        jurisdiction.ts          # FieldConfig, JurisdictionSummary, ConfigTypeResponse
        field.ts                 # FieldDetail, XPathEntry, DependencyRef, JavaReference
        translation.ts           # TranslationResult
        dashboard.ts             # DashboardStats, JurisdictionStatus, LogEntry
        chat.ts                  # ChatMessage, ChatSession, ChatSessionDetail
      components/                # React UI components
```

---

## How the System Works End-to-End

### 1. Jurisdiction Configuration

`jurisdiction.json` at the project root defines each regulatory jurisdiction:

- **id / name / display_name**: Identifier and labels (e.g., `hkma`, `HKMA`, `Hong Kong Monetary Authority`)
- **git_path / lib_path**: Paths to the jurisdiction's main code repo and shared library repo
- **module_type**: Classification (`dtcc/iso`, `exception-service`)
- **configs**: A dictionary of config types (e.g., `TradeState`, `Valuation`), each containing an array of field definitions

Each field has:
- **header**: Human-readable business name (e.g., `"Effective Date"`)
- **field_name**: Code-level variable name (e.g., `"N_EFFECTIVE_DATE"`)
- **asset_classes**: Which asset classes this field applies to (e.g., `["InterestRate", "CDS", "FX"]`)

### 2. Parsing Pipeline

The orchestrator layer scans and parses code repositories:

1. **ModuleScanner** (`scanner.py`): Discovers `.java` and `.xsl/.xslt` files in a directory tree. Detects multi-module projects (by pom.xml/build.gradle markers). Identifies cross-language references where Java code loads XSLT files (via `StreamSource`, `getResourceAsStream`, `ClassPathResource`, or string literals).

2. **JavaParser** (`parsers/java_parser.py`): Regex-based parser that extracts:
   - Method calls (`obj.method()`)
   - DTO unmarshalling (`unmarshal(..., MyClass.class)`)
   - Field mappings (`target.setFoo(source.getFoo())`)
   - Constant references (`MessageKey.N_EFFECTIVE_DATE`)
   - String literal field keys (`"N_EFFECTIVE_DATE"`)
   - XSLT file references (`"trade_transform.xsl"`)

3. **XsltParser** (`parsers/xslt_parser.py`): lxml-based parser that extracts:
   - Template definitions (name and match attributes)
   - `xsl:value-of` selects (field extraction via XPath)
   - `xsl:call-template` invocations
   - `xsl:copy-of` bulk mappings

4. **Stitcher** (`stitcher.py`): Connects Java and XSLT findings into a unified lineage graph. Uses canonical key matching to link fields across languages and repositories:
   - Normalizes names: `N_EFFECTIVE_DATE` matches `nEffectiveDate` matches `effectiveDate`
   - Strips qualifiers: `MessageKey.N_EFFECTIVE_DATE` becomes `N_EFFECTIVE_DATE`
   - Handles cross-repo linking when the same field name appears in different repos
   - Builds `LineageNode` and `LineageEdge` objects with typed relationships (CALLS, DERIVED_FROM, TRANSFORMS, LOADS_XSLT, CROSS_REPO, UNMARSHALS_TO)

5. **ParseCache** (`services/cache.py`): In-memory thread-safe cache storing parsed results per jurisdiction. Holds `java_findings`, `xslt_findings`, `lineage` (stitched graph), and `xpath_index`.

### 3. API Layer

The FastAPI backend loads `jurisdiction.json` on startup, then exposes endpoints for:
- Browsing jurisdictions and their field configurations
- Retrieving detailed field information (XSLT logic, XPath entries, Java references, dependencies)
- XPath reverse lookup (find all XPaths referencing a field)
- Translation explanations (code-to-business-language, currently a stub)
- Triggering batch parse of all jurisdictions (runs in background thread)
- Dashboard stats and live SSE logs during parsing
- Chat sessions with LLM-powered responses (LLM is currently a stub)
- LLM field description generation

### 4. Frontend

The React TypeScript frontend consumes the API:
- **Zustand store** (`appStore.ts`) holds UI state: selected jurisdiction, config type, field, asset class, view mode, chat state
- **React Query hooks** fetch data from the API with caching and automatic refetch
- **API client** (`client.ts`) wraps `fetch` with a `/api` base path prefix
- The UI follows an AppShell pattern with Header, Sidebar, and Main content areas
- Views include an Explorer (browse jurisdictions/fields) and a Dashboard (parse status/graphs)

---

## Key Concepts

### Jurisdictions
Regulatory bodies (HKMA, MAS, DTCC) each with their own code repos and field configurations. Defined in `jurisdiction.json`.

### Config Types
Categories of field configurations within a jurisdiction. Currently `TradeState` (trade lifecycle fields) and `Valuation` (mark-to-market and collateral fields).

### Fields
Each field has two names:
- **header**: Business name shown to users (e.g., `"Effective Date"`)
- **field_name**: Code variable name used in Java/XSLT (e.g., `"N_EFFECTIVE_DATE"`)

### Canonical Key Matching
The stitcher normalizes field names to enable cross-language matching:
- `N_EFFECTIVE_DATE` (XSLT) matches `MessageKey.N_EFFECTIVE_DATE` (Java constant)
- `nEffectiveDate` (Java camelCase) matches `N_EFFECTIVE_DATE` (UPPER_SNAKE)
- Single-letter prefixes are stripped: `N_EFFECTIVE_DATE` also matches `EFFECTIVE_DATE` and `effectiveDate`

### XPath Reverse Index
An index built from XSLT findings that maps field names to their XPath expressions. Used by the field detail view and the XPath lookup endpoint to show where a field is referenced in XSLT transformations.

### Lineage Graph
The output of stitching: a directed graph of `LineageNode` (classes, methods, fields, constants, templates) connected by `LineageEdge` (CALLS, DERIVED_FROM, TRANSFORMS, LOADS_XSLT, CROSS_REPO, UNMARSHALS_TO). Can be exported to PyVis HTML, Neo4j Cypher, or JSON.

---

## How to Run

### Backend

```bash
cd synapse-trace
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd synapse-trace/frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

### Orchestrator CLI (Standalone)

```bash
# Auto-discover modules in a project
python -m orchestrator.parser --project /path/to/project-root

# Scan specific directories
python -m orchestrator.parser --scan src/

# Multi-repo via JSON config
python -m orchestrator.parser --config repos.json

# Quick trace (programmatic)
from orchestrator.quick_trace import trace_project
result = trace_project(main="/code/my-app", libs=["/code/lib-fields"])
result.print_summary()
result.to_json("output/lineage.json")
```

---

## How to Extend

### Adding a New Jurisdiction

1. Add a new entry to `jurisdiction.json` with `id`, `name`, `display_name`, `git_path`, `lib_path`, `module_type`, and `configs` (with `TradeState` and/or `Valuation` fields).
2. Restart the backend. The new jurisdiction will be loaded automatically.

### Connecting an LLM

Edit `src/api/services/llm_service.py`. Replace the `_call_llm` method in the `LLMService` class:

```python
async def _call_llm(self, prompt: str, context: dict | None = None) -> str:
    # Example for OpenAI:
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

Also update `generate_business_description` and `answer_chat_query` to use `_call_llm` instead of returning hardcoded strings.

### Switching from SQLite to MSSQL

Edit `src/api/database.py`:

```python
# Replace:
DATABASE_URL = "sqlite:///./synapse_trace.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# With:
DATABASE_URL = "mssql+pyodbc://user:pass@host/dbname?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(DATABASE_URL)
```

Install the MSSQL driver: `pip install pyodbc`

### Adding a New Parser

Use the pluggable parser registry in `quick_trace.py`:

```python
from orchestrator.quick_trace import register_parser

class GroovyParser:
    def __init__(self, repo_name: str = "") -> None:
        self._repo_name = repo_name

    def parse_file(self, file_path: Path) -> list:
        # Return list of JavaFinding or XsltFinding objects
        ...

register_parser(".groovy", GroovyParser)
```

### Adding New API Endpoints

1. Create a schema in `src/api/schemas/`
2. Create a service in `src/api/services/`
3. Create a router in `src/api/routers/`
4. Register the router in `src/api/main.py` with `app.include_router()`

### Adding Frontend Features

1. Add TypeScript types in `frontend/src/types/`
2. Add API functions in `frontend/src/api/`
3. Add React Query hooks in `frontend/src/hooks/`
4. Add UI state to the Zustand store in `frontend/src/stores/appStore.ts` if needed
5. Create components in `frontend/src/components/`
