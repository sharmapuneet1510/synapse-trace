# Synapse Trace — Frontend Guide

A practical guide to using the Synapse Trace web interface for financial operations teams and developers integrating with the system.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Application Layout](#application-layout)
3. [Explorer View — Step-by-Step](#explorer-view--step-by-step)
4. [Business View vs Technical View](#business-view-vs-technical-view)
5. [Variable Trace Graph](#variable-trace-graph)
6. [Chat Assistant](#chat-assistant)
7. [Dashboard View](#dashboard-view)
8. [Triggering a Parse](#triggering-a-parse)
9. [Live Parse Logs](#live-parse-logs)
10. [Frontend Architecture (Developer Reference)](#frontend-architecture-developer-reference)
11. [Adding a New UI Feature](#adding-a-new-ui-feature)

---

## Getting Started

### Run the frontend

```bash
cd synapse-trace/frontend
npm install
npm run dev
```

The app is available at `http://localhost:5173`. It proxies all `/api/*` requests to the FastAPI backend at `http://localhost:8000`.

Make sure the backend is running before using the app:

```bash
cd synapse-trace
uvicorn src.api.main:app --reload --port 8000
```

### First steps after launch

1. The app loads in **Explorer** mode with no field selected.
2. Before field detail and lineage data are available, you must trigger a **batch parse** (see [Triggering a Parse](#triggering-a-parse)).
3. After parsing, select a jurisdiction → report type → field to explore.

---

## Application Layout

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: [Synapse Trace]  [Explorer] [Dashboard]   [Chat]  │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  SIDEBAR         │  MAIN PANEL                              │
│  (~280px)        │                                          │
│                  │  FieldDetailPanel                        │
│  Jurisdiction    │   └─ Header (name, ID badge, toggles)   │
│  Report Type     │   └─ Business View (default)            │
│  Fields list     │       └─ Business Translation tabs      │
│                  │       └─ Quick stats                     │
│                  │       └─ Dependencies                    │
│                  │   └─ Technical View                      │
│                  │       └─ XSLT Logic                     │
│                  │       └─ Dependencies                    │
│                  │       └─ Input XPaths table              │
│                  │       └─ Variable Trace Graph            │
│                  │                                          │
└──────────────────┴──────────────────────────────────────────┘
                                          [Chat Drawer →]
```

---

## Explorer View — Step-by-Step

### Step 1 — Select a Jurisdiction

The left sidebar shows a searchable grid of all configured jurisdictions (e.g., HKMA, MAS, DTCC). Click any card to select it. The card highlights in red when active.

If there are more than 5 jurisdictions, a search box appears at the top of the grid to filter by name or ID.

### Step 2 — Select a Report Type

Once a jurisdiction is selected, a tab bar appears below showing the available config types (e.g., **TradeState**, **Valuation**). Click a tab to load its fields.

### Step 3 — Select a Field

The field list appears below the report type tabs. Each entry shows:
- A numbered badge (red when active)
- The business name of the field (e.g., "Effective Date")
- An expand chevron

Click any field to load its details in the main panel.

### Step 4 — Browse Field Details

The main panel updates immediately with:
- The **field business name** as a large heading
- A monospaced **code badge** showing the variable name (e.g., `N_EFFECTIVE_DATE`)
- A colored **config type badge** (e.g., `TradeState`)
- An **Asset Class selector** if the field applies to multiple asset classes
- A **Business / Technical toggle** in the top-right corner

---

## Business View vs Technical View

### Business View (default)

The default view is designed for operations and compliance users who need to understand **what a field means** without reading code.

**Business Translation** is displayed inline, with tabs for:

| Tab | Content |
|-----|---------|
| **Derivation** | Where the field value comes from — source systems, calculation logic in business terms |
| **Reporting Logic** | Step-by-step description of how the field is populated and validated for submission |
| **Enrichment** | Internal transformations, lookups, or enrichment that modify the raw value |
| **Downstream** | Which systems consume this field after reporting (downstream mapping) |
| **Examples** | Concrete worked examples: what the field value looks like for different trade types |
| **Operations** | Guidance for the operations team on common issues, investigations, and overrides |

Below the translation, a **quick stats row** shows:
- Number of dependencies
- Number of data sources (XPath entries)
- Active jurisdiction

If the field has dependencies, a **dependency list** is shown below the stats row.

> **Note:** Translation content is LLM-generated. Until an LLM is connected (see `llm_service.py`), placeholder stub text is shown. The placeholders are clearly marked with `[Stub Response]`.

### Technical View

Switch to **Technical** using the toggle in the top-right corner. This view is for engineers and data lineage analysts.

**Sections:**

1. **XSLT Logic** — The raw XSLT snippet that extracts this field, with the file name and line number.
2. **Dependencies** — Fields this one depends on, with relationship type and source file.
3. **Input XPaths / Data Points** — Table of all XPath expressions that feed this field, showing the source file, XPath query, template name, and output element.
4. **Variable Trace Graph** — Interactive force-directed graph showing the full lineage subgraph for this variable (see [Variable Trace Graph](#variable-trace-graph)).

---

## Variable Trace Graph

The **Variable Trace** section appears in the Technical View. It lets you explore exactly which Java classes, methods, constants, XSLT templates, and files are connected to a field variable across the entire codebase.

### Pre-populated from the field

When you switch to Technical View with a field selected, the trace inputs are pre-populated with the current field name and jurisdiction. Click **Trace →** to run immediately.

### Running a custom trace

You can also type a different variable name or jurisdiction directly into the trace panel inputs:

| Input | Description |
|-------|-------------|
| **Variable Name** | The field/variable name to trace (e.g., `N_EFFECTIVE_DATE`) |
| **Jurisdiction** | Which parsed codebase to search (e.g., `hkma`) |
| **Extra Aliases** | Comma-separated additional name variants the system won't auto-derive (e.g., `effectiveDate, EFFECTIVE_DT`) |

Press **Enter** or click **Trace →** to run. The system automatically expands the input name to all canonical forms (camelCase ↔ UPPER_SNAKE, prefix-stripped variants, etc.) before searching.

### Reading the graph

**Nodes** represent code entities:

| Color | Node Type | Meaning |
|-------|-----------|---------|
| Orange border | `JAVA_CLASS` | A Java class |
| Amber border | `JAVA_METHOD` | A method inside a Java class |
| Red border | `JAVA_FIELD` | A field/attribute on a Java class |
| Purple border | `JAVA_CONSTANT` | A static constant (e.g., `MessageKey.N_EFFECTIVE_DATE`) |
| Green border | `DTO` | A data transfer object class |
| Blue border | `XSLT_FILE` | An XSLT stylesheet file |
| Cyan border | `XSLT_TEMPLATE` | A named XSLT template |
| Indigo border | `XSLT_FIELD` | A field extracted inside an XSLT template |

**Arrows** represent relationships:

| Color | Edge Type | Meaning |
|-------|-----------|---------|
| Dark red | `DERIVED_FROM` | This node's value is derived from the target |
| Blue | `CALLS` | This method/class calls the target |
| Amber | `TRANSFORMS` | XSLT template transforms target data |
| Green | `UNMARSHALS_TO` | Java unmarshal operation targets this DTO |
| Purple | `CROSS_REPO` | Link crosses repository boundary |
| Cyan | `LOADS_XSLT` | Java code loads this XSLT file |

### Graph controls

| Action | How |
|--------|-----|
| **Zoom in/out** | Scroll wheel, or use `+`/`−` buttons (top-right) |
| **Pan** | Click and drag on the background |
| **Move a node** | Click and drag the node rectangle |
| **Select a node** | Click a node to show detail overlay at the bottom |
| **Deselect** | Click the node again, or press the `✕` in the detail overlay |
| **Reset view** | Click the reset button (circular arrow, top-right) |

### Detail overlay

Clicking a node opens a detail panel at the bottom of the graph showing:
- Full label and node type
- File path (last 2 path segments) and line number
- Code snippet (first 200 characters)

---

## Chat Assistant

The **Chat** button in the header bar opens a chat drawer from the right side of the screen. Use it to ask questions about fields, regulations, or the data lineage in natural language.

### Context awareness

When a field is selected in the Explorer, the chat automatically carries that context. New messages sent while a field is open will tag the message with:
- `jurisdiction_id` — the active jurisdiction
- `field_name` — the active field

The assistant's response can therefore reference the specific field without you needing to spell it out.

### Session management

- A new session is created automatically if none is active.
- Previous sessions appear in a dropdown at the top of the chat drawer.
- Sessions persist in the database and survive page reloads.
- Click the trash icon to delete a session and all its messages.

### Current status

The LLM backend is a **stub** by default. Responses will show `[Stub Response]` until you wire in a real LLM (see `src/api/services/llm_service.py` → `_call_llm()`).

---

## Dashboard View

Click **Dashboard** in the header to switch to the dashboard panel.

### Tabs

| Tab | Content |
|-----|---------|
| **Overview** | Matrix table of all jurisdictions — status, Java findings, XSLT findings, nodes, edges, last parsed time. Click **Explore** to jump to that jurisdiction in the Explorer. |
| **Live Logs** | Real-time streaming log of the current or most recent batch parse. Logs auto-update every second. |
| **Nodes** | Paginated table of all lineage graph nodes for a selected jurisdiction. |
| **Edges** | Paginated table of all lineage graph edges for a selected jurisdiction. |

### Status badges

| Badge | Meaning |
|-------|---------|
| `idle` | No parse has run yet |
| `running` | A batch parse is in progress |
| `ready` | Parse completed successfully |
| `error` | Parse failed for this jurisdiction |

---

## Triggering a Parse

Before field detail, lineage data, and the trace graph are available, you must run a **batch parse**.

**From the Dashboard:**

1. Switch to the **Dashboard** view.
2. Click the **Trigger Parse** button.
3. The button shows a spinner while the parse is running.
4. Switch to the **Live Logs** tab to watch progress in real time.
5. When all jurisdictions show `ready` status, the parse is complete.

**What happens:**
- The backend scans all `git_path` and `lib_path` directories for each jurisdiction.
- Java and XSLT files are parsed and findings extracted.
- The Stitcher links Java and XSLT findings into a unified lineage graph.
- Results are cached in memory (persisted until the server restarts).

**Expected duration:** Varies by codebase size. A typical regulatory reporting project with 200–500 Java files and 50–100 XSLT files takes 15–60 seconds per jurisdiction.

---

## Live Parse Logs

During a batch parse, the **Live Logs** tab streams log entries in real time using Server-Sent Events (SSE). Each log entry shows:

- **Timestamp**
- **Level** (`info`, `warning`, `error`)
- **Message** — what the parser is doing (e.g., `"Parsed TradeMapper.java: 15 findings"`)
- **Jurisdiction** — which jurisdiction the log belongs to (color-coded)

Between log entries, the server sends heartbeat events every second with the current `batch_status`. The frontend uses these to update the status badge in real time without polling.

Log entries are retained in memory for the session (up to 500 entries). Navigating away and back to Live Logs will replay all entries from the current parse run.

---

## Frontend Architecture (Developer Reference)

### State Management

Global UI state lives in a single **Zustand store** at `frontend/src/stores/appStore.ts`:

```typescript
// Reading state
const { jurisdictionId, fieldName, detailViewMode } = useAppStore();

// Writing state
const { setJurisdiction, setField, setDetailViewMode } = useAppStore();
setDetailViewMode('technical');
```

| State field | Type | Description |
|-------------|------|-------------|
| `jurisdictionId` | `string \| null` | Selected jurisdiction ID |
| `configType` | `string \| null` | Selected config type (e.g. `TradeState`) |
| `fieldName` | `string \| null` | Selected field variable name |
| `assetClass` | `string \| null` | Selected asset class filter |
| `activeView` | `'explorer' \| 'dashboard'` | Which top-level view is shown |
| `detailViewMode` | `'business' \| 'technical'` | Business or technical detail view |
| `chatOpen` | `boolean` | Whether the chat drawer is open |
| `chatSessionId` | `string \| null` | Active chat session UUID |

### API Client

All API calls go through `frontend/src/api/client.ts`:

```typescript
import { api } from './client';

// GET request
const data = await api.get<MyType>('/some/endpoint');

// POST request
const result = await api.post<ResponseType>('/some/endpoint', { key: 'value' });

// DELETE request
await api.delete('/some/endpoint');
```

The base URL is `/api` — the Vite dev server proxies this to `http://localhost:8000`.

### React Query Hooks

Data fetching uses **@tanstack/react-query** with custom hooks in `frontend/src/hooks/`:

```typescript
// Example: load field detail
import { useFieldDetail } from '../../hooks/useFieldDetail';
const { data: detail, isLoading, isError } = useFieldDetail(jurisdictionId, fieldName);

// Example: mutation (trace)
import { useTraceVariable } from '../../hooks/useTrace';
const traceMutation = useTraceVariable();
traceMutation.mutate({ variable_name: 'N_EFFECTIVE_DATE', jurisdiction_id: 'hkma' });
```

| Hook | Purpose | Cache key |
|------|---------|-----------|
| `useJurisdictions()` | All jurisdictions | `['jurisdictions']` |
| `useConfigType(jid, ct)` | Fields for a config type | `['configType', jid, ct]` |
| `useFieldDetail(jid, fname)` | Single field detail | `['fieldDetail', jid, fname]` |
| `useTranslation(fname, jid)` | Business translation | `['translation', jid, fname]` |
| `useDashboardStats()` | Dashboard stats (polls 3s) | `['dashboardStats']` |
| `useParseLogs()` | Parse log entries (polls 2s) | `['parseLogs', limit]` |
| `useNodes(jid)` | Lineage nodes | `['nodes', jid, limit, offset]` |
| `useEdges(jid)` | Lineage edges | `['edges', jid, limit, offset]` |
| `useTraceVariable()` | Variable trace (mutation) | n/a (mutation) |
| `useChatSessions()` | All chat sessions | `['chatSessions']` |
| `useChatSession(id)` | Single session + messages | `['chatSession', id]` |
| `useSendMessage()` | Send chat message (mutation) | n/a |
| `useCreateSession()` | Create chat session (mutation) | n/a |
| `useDeleteSession()` | Delete session (mutation) | n/a |

### Component Tree

```
App
└── AppShell
    ├── Header
    ├── Sidebar
    │   ├── JurisdictionSelector
    │   ├── ConfigTypeTabs
    │   └── FieldList
    ├── Main panel
    │   ├── FieldDetailPanel  (Explorer view)
    │   │   ├── AssetClassSelector
    │   │   ├── XsltLogicBlock        (technical view)
    │   │   ├── DependencyList
    │   │   ├── InputXPathsTable      (technical view)
    │   │   └── TracePanel            (technical view)
    │   │       └── LineageGraph
    │   └── DashboardPanel  (Dashboard view)
    └── ChatPanel (drawer, always mounted)
```

---

## Adding a New UI Feature

Follow this pattern to add a new data-backed UI feature:

### 1. Define the TypeScript type

```typescript
// frontend/src/types/my-feature.ts
export interface MyFeatureData {
  field_a: string;
  field_b: number;
}
```

### 2. Add the API function

```typescript
// frontend/src/api/my-feature.ts
import { api } from './client';
import type { MyFeatureData } from '../types/my-feature';

export function fetchMyFeature(id: string): Promise<MyFeatureData> {
  return api.get<MyFeatureData>(`/my-feature/${id}`);
}
```

### 3. Add the React Query hook

```typescript
// frontend/src/hooks/useMyFeature.ts
import { useQuery } from '@tanstack/react-query';
import { fetchMyFeature } from '../api/my-feature';

export function useMyFeature(id: string | null) {
  return useQuery({
    queryKey: ['myFeature', id],
    queryFn: () => fetchMyFeature(id!),
    enabled: !!id,
  });
}
```

### 4. Build the component

```tsx
// frontend/src/components/main/MyFeaturePanel.tsx
import { useMyFeature } from '../../hooks/useMyFeature';

export default function MyFeaturePanel({ id }: { id: string }) {
  const { data, isLoading } = useMyFeature(id);
  if (isLoading) return <div>Loading...</div>;
  if (!data) return null;
  return <div className="glass-card">{data.field_a}</div>;
}
```

### 5. Add it to the detail panel

Import and render inside `FieldDetailPanel.tsx` under the appropriate view section (business or technical).

---

## CSS Design Tokens

The app uses a red/white theme defined in `frontend/src/index.css`:

| Class | Usage |
|-------|-------|
| `.glass-card` | Card containers — white bg, subtle border, rounded corners |
| `.section-bar` | Section header bars — red gradient background, white text |
| `.section-count` | Muted count badge shown inside a section bar |
| `.translation-tabs` | Horizontal tab bar for business translation tabs |
| `.view-toggle` | Business/Technical toggle button group |
| `.jurisdiction-card` | Jurisdiction grid card in the sidebar |
| `.chat-drawer` | Slide-in chat panel from the right |

Brand color: `#dc2626` (Tailwind `red-600`). Use `text-brand`, `border-brand`, `bg-brand` utilities.
