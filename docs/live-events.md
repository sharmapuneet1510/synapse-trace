# Live Events — SSE & Event Bus Guide

Synapse Trace streams real-time parse progress to the frontend via **Server-Sent Events (SSE)** and exposes an internal **EventBus** for orchestrator components to emit events as they work. This document covers both the frontend consumer pattern and the backend emitter pattern.

---

## Table of Contents

1. [Overview](#overview)
2. [SSE Endpoint](#sse-endpoint)
3. [Consuming SSE in the Browser](#consuming-sse-in-the-browser)
4. [Consuming SSE in the React Frontend](#consuming-sse-in-the-react-frontend)
5. [Event Types Reference](#event-types-reference)
6. [Backend Event Bus](#backend-event-bus)
7. [Emitting Events from Orchestrator Components](#emitting-events-from-orchestrator-components)
8. [Dashboard Stats Polling](#dashboard-stats-polling)
9. [Combining SSE + Polling](#combining-sse--polling)
10. [Integration Examples](#integration-examples)

---

## Overview

Live progress updates flow through two mechanisms:

```
Orchestrator (Python)
  └─ scanner.py, java_parser.py, xslt_parser.py, stitcher.py
       │  emit(event_type, data)
       ▼
  live_events.EventBus  (in-memory, thread-safe deque)
       │
       ▼
  parse_service.py  (batch parse thread writes log entries)
       │  parse_cache.add_log(...)
       ▼
  ParseCache.logs  (rolling buffer, up to 500 entries)
       │
       ▼
  GET /api/dashboard/live  (SSE endpoint, polls cache every 1s)
       │  data: {"timestamp":...,"level":"info","message":"..."}
       │  data: {"type":"heartbeat","batch_status":"running",...}
       ▼
  Browser EventSource
       └─ React component updates in real time
```

---

## SSE Endpoint

### `GET /api/dashboard/live`

A persistent HTTP connection that streams newline-delimited JSON events.

**Response type:** `text/event-stream`

**Event stream format:**

```
data: {"timestamp":"2025-03-15T10:30:01.234","level":"info","message":"Starting parse for HKMA","jurisdiction_id":"hkma"}

data: {"type":"heartbeat","batch_status":"running","timestamp":"2025-03-15T10:30:02.000"}

data: {"timestamp":"2025-03-15T10:30:03.456","level":"info","message":"Parsed TradeMapper.java: 15 findings","jurisdiction_id":"hkma"}

data: {"timestamp":"2025-03-15T10:30:04.000","level":"warning","message":"File not found: /repos/hkma/missing.xsl","jurisdiction_id":"hkma"}

data: {"type":"heartbeat","batch_status":"done","timestamp":"2025-03-15T10:30:45.000"}
```

**Two event shapes are interleaved:**

### Log entry event

Emitted when a new log message is added during parsing:

```json
{
  "timestamp": "2025-03-15T10:30:03.456",
  "level": "info",
  "message": "Parsed TradeMapper.java: 15 findings",
  "jurisdiction_id": "hkma"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO 8601 string | When the event occurred |
| `level` | `"info"` \| `"warning"` \| `"error"` | Severity |
| `message` | string | Human-readable description |
| `jurisdiction_id` | string \| null | Which jurisdiction this log belongs to |

### Heartbeat event

Sent every second regardless of activity. Use it to check current batch status and detect connection health:

```json
{
  "type": "heartbeat",
  "batch_status": "running",
  "timestamp": "2025-03-15T10:30:02.000"
}
```

| Field | Type | Values |
|-------|------|--------|
| `type` | string | Always `"heartbeat"` |
| `batch_status` | string | `"idle"` \| `"running"` \| `"done"` \| `"error"` |
| `timestamp` | ISO 8601 string | Server time |

---

## Consuming SSE in the Browser

Use the native `EventSource` API. No library needed.

### Minimal example

```javascript
const es = new EventSource('http://localhost:8000/api/dashboard/live');

es.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'heartbeat') {
    console.log('Batch status:', data.batch_status);
    return;
  }

  // Log entry
  console.log(`[${data.level.toUpperCase()}] [${data.jurisdiction_id}] ${data.message}`);
};

es.onerror = (err) => {
  console.error('SSE connection error', err);
  es.close();
};

// Clean up when done
function stopListening() {
  es.close();
}
```

### Filter log entries by jurisdiction

```javascript
es.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'heartbeat') return;
  if (data.jurisdiction_id !== 'hkma') return;

  appendLogEntry(data);
};
```

### Detect parse completion

```javascript
let lastStatus = 'idle';

es.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'heartbeat') {
    if (lastStatus === 'running' && data.batch_status === 'done') {
      console.log('Parse complete — refresh data');
      es.close();
    }
    lastStatus = data.batch_status;
  }
};
```

### Auto-reconnect with exponential backoff

`EventSource` reconnects automatically on disconnect. If you need manual control:

```javascript
let delay = 1000;

function connect() {
  const es = new EventSource('/api/dashboard/live');

  es.onopen = () => { delay = 1000; };

  es.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleEvent(data);
  };

  es.onerror = () => {
    es.close();
    setTimeout(() => {
      delay = Math.min(delay * 2, 30000); // max 30s
      connect();
    }, delay);
  };
}

connect();
```

---

## Consuming SSE in the React Frontend

The existing frontend uses **polling** (`useDashboardStats` refetches every 3 seconds, `useParseLogs` every 2 seconds). If you want to add SSE-based live updates to a custom component, here is the pattern:

### Custom hook using EventSource

```typescript
// frontend/src/hooks/useLiveLogs.ts
import { useState, useEffect, useRef } from 'react';
import type { LogEntry } from '../types/dashboard';

export function useLiveLogs(enabled: boolean) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [batchStatus, setBatchStatus] = useState<string>('idle');
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const es = new EventSource('/api/dashboard/live');
    esRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'heartbeat') {
        setBatchStatus(data.batch_status);
        return;
      }

      setLogs((prev) => {
        const next = [...prev, data as LogEntry];
        return next.slice(-500); // keep last 500
      });
    };

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [enabled]);

  const clear = () => setLogs([]);

  return { logs, batchStatus, clear };
}
```

### Use in a component

```tsx
import { useLiveLogs } from '../../hooks/useLiveLogs';

export default function LiveLogPanel() {
  const { logs, batchStatus, clear } = useLiveLogs(true);

  return (
    <div>
      <div>Status: <strong>{batchStatus}</strong></div>
      <button onClick={clear}>Clear</button>
      <div className="font-mono text-xs space-y-0.5">
        {logs.map((log, i) => (
          <div key={i} className={log.level === 'error' ? 'text-red-600' : 'text-gray-700'}>
            <span className="text-gray-400">{log.timestamp.slice(11, 23)}</span>{' '}
            <span className="uppercase font-bold text-[9px]">{log.level}</span>{' '}
            {log.jurisdiction_id && (
              <span className="text-brand">[{log.jurisdiction_id.toUpperCase()}]</span>
            )}{' '}
            {log.message}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Close SSE when parse completes

```typescript
useEffect(() => {
  if (batchStatus === 'done' && esRef.current) {
    esRef.current.close();
    // optionally: invalidate React Query caches to refresh stats
    queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
  }
}, [batchStatus]);
```

---

## Event Types Reference

These are the event type constants defined in `src/orchestrator/live_events.py`. They flow through the EventBus but are not all surfaced via the SSE endpoint — the SSE endpoint only streams log entries from `ParseCache.logs`.

### Scanner events

| Constant | Value | Payload fields | Description |
|----------|-------|----------------|-------------|
| `SCAN_START` | `"scan_start"` | `path`, `name` | Project or module scan begins |
| `SCAN_FILE` | `"scan_file"` | `path`, `type` | File discovered (`java` or `xslt`) |
| `SCAN_REF` | `"scan_ref"` | `from_file`, `to_file` | Cross-language reference detected |
| `SCAN_COMPLETE` | `"scan_complete"` | `path`, `java_count`, `xslt_count` | Scan finished |

### Parser events

| Constant | Value | Payload fields | Description |
|----------|-------|----------------|-------------|
| `PARSE_START` | `"parse_start"` | `file`, `parser` | File parsing begins |
| `PARSE_FINDING` | `"parse_finding"` | `field`, `type`, `parser`, `file` | A finding was extracted |
| `PARSE_COMPLETE` | `"parse_complete"` | `file`, `count`, `parser` | File parsing done |

### Stitcher events

| Constant | Value | Payload fields | Description |
|----------|-------|----------------|-------------|
| `STITCH_START` | `"stitch_start"` | `java_count`, `xslt_count` | Stitching begins |
| `NODE_ADDED` | `"node_added"` | `id`, `label`, `type` | A node was created in the graph |
| `EDGE_ADDED` | `"edge_added"` | `source`, `target`, `type` | An edge was created |
| `MATCH_FOUND` | `"match_found"` | `java_key`, `xslt_key` | Cross-language field match found |
| `STITCH_PHASE` | `"stitch_phase"` | `phase` | Phase transition (e.g., `"java_nodes"`, `"xslt_nodes"`, `"edges"`) |
| `STITCH_COMPLETE` | `"stitch_complete"` | `nodes`, `edges` | Stitching done |

### Trace events

| Constant | Value | Payload fields | Description |
|----------|-------|----------------|-------------|
| `TRACE_START` | `"trace_start"` | `variable`, `jurisdiction` | Trace operation begins |
| `LIB_SEARCH` | `"lib_search"` | `class_name`, `lib` | Searching library for a class |
| `LIB_FOUND` | `"lib_found"` | `class_name`, `lib`, `file` | Class found in library |
| `FILTER_START` | `"filter_start"` | `seed_count` | Subgraph BFS begins |
| `FILTER_COMPLETE` | `"filter_complete"` | `nodes`, `edges` | Subgraph extracted |
| `TRACE_COMPLETE` | `"trace_complete"` | `nodes`, `edges`, `variable` | Full trace done |

### Stats event

| Constant | Value | Payload fields | Description |
|----------|-------|----------------|-------------|
| `STATS_UPDATE` | `"stats_update"` | (all counters) | Periodic snapshot of all counters |

---

## Backend Event Bus

`src/orchestrator/live_events.py` provides a module-level singleton event bus.

### Quick start

```python
from src.orchestrator.live_events import emit, subscribe, enable, disable, stats

# Enable before starting a parse (disabled by default to avoid overhead)
enable()

# Emit an event from anywhere in the orchestrator
emit("node_added", {"id": "java::class::Foo", "label": "Foo", "type": "JAVA_CLASS"})

# Get current counters
current = stats()
# {
#   "files_scanned": 42,
#   "java_findings": 180,
#   "xslt_findings": 65,
#   "nodes_created": 120,
#   "edges_created": 95,
#   "matches_found": 38,
#   "libs_searched": 12,
#   "classes_resolved": 10
# }

# Disable when done
disable()
```

### Subscribe to events (generator)

```python
from src.orchestrator.live_events import subscribe

# In a background thread — yields events as they arrive
for event in subscribe(include_history=True):
    print(f"[{event.event_type}] {event.data}")
    # Process event...
    # Note: this loop runs forever until the thread is killed
```

### Access event history

```python
from src.orchestrator.live_events import get_bus

bus = get_bus()
history = bus.get_history()
# Returns list of dicts: [{"event": "node_added", "data": {...}, "ts": 1710499200.0}, ...]
```

### Reset for a new parse run

```python
from src.orchestrator.live_events import reset, enable

reset()   # clear history and zero all counters
enable()  # ensure emission is on
```

### EventBus API

```python
from src.orchestrator.live_events import get_bus

bus = get_bus()
bus.enable()                        # start emitting
bus.disable()                       # stop emitting (no-op emit calls)
bus.emit("event_type", {"k": "v"}) # emit an event
bus.subscribe()                     # generator: yields TraceEvent objects
bus.get_history()                   # list of dicts for all stored events
bus.get_stats()                     # dict of all counters
bus.reset()                         # clear history, zero counters
```

---

## Emitting Events from Orchestrator Components

To add live progress events to a new parser or processing step:

### Import and emit

```python
from src.orchestrator import live_events

def parse_my_file(path: Path) -> list:
    live_events.emit(live_events.PARSE_START, {"file": str(path), "parser": "my_parser"})
    findings = []

    # ... parsing work ...

    for finding in raw_findings:
        findings.append(finding)
        live_events.emit(live_events.PARSE_FINDING, {
            "field": finding.field_name,
            "type": finding.finding_type,
            "parser": "my_parser",
            "file": str(path),
        })

    live_events.emit(live_events.PARSE_COMPLETE, {
        "file": str(path),
        "count": len(findings),
        "parser": "my_parser",
    })
    return findings
```

### Guard with `enabled` check for performance

The bus no-ops when disabled, so you don't need to guard — but for very hot loops where even a function call is too much:

```python
if live_events.get_bus().enabled:
    live_events.emit("scan_file", {"path": str(f), "type": "java"})
```

### Custom event types

You can emit any string as an event type, not just the constants:

```python
live_events.emit("groovy_finding", {"field": "tradeId", "file": "mapper.groovy"})
```

The SSE endpoint does not filter by event type — all events are accessible via `subscribe()` or `get_history()`.

---

## Dashboard Stats Polling

In addition to SSE, the frontend polls two endpoints on short intervals for dashboard data:

### `GET /api/dashboard/stats` — every 3 seconds

Returns aggregate stats across all jurisdictions. The frontend React Query hook:

```typescript
// Polls every 3 seconds automatically
const { data: stats } = useDashboardStats(3000);
```

You can change the poll interval:

```typescript
const { data: stats } = useDashboardStats(10000); // every 10 seconds
```

Or disable polling when parse is complete:

```typescript
const [pollingEnabled, setPollingEnabled] = useState(true);

const { data: stats } = useDashboardStats(pollingEnabled ? 3000 : false);

useEffect(() => {
  if (stats?.batch_status === 'done') {
    setPollingEnabled(false);
  }
}, [stats?.batch_status]);
```

### `GET /api/parse/logs?limit=100` — every 2 seconds

Returns recent parse log entries from the in-memory log buffer:

```typescript
const { data: logs } = useParseLogs(200, 2000); // 200 entries, poll every 2s
```

---

## Combining SSE + Polling

The recommended pattern for a full live dashboard:

```
SSE  → high-frequency log entries (streaming, no delay)
Poll → stats/counts (every 3–5s, simple and reliable)
```

```typescript
export default function LiveDashboard() {
  // SSE for log stream
  const { logs, batchStatus } = useLiveLogs(true);

  // Polling for aggregate stats (automatically stops when done)
  const [pollInterval, setPollInterval] = useState<number | false>(3000);
  const { data: stats } = useDashboardStats(pollInterval);

  useEffect(() => {
    if (batchStatus === 'done') {
      setPollInterval(false); // stop polling
    }
  }, [batchStatus]);

  return (
    <div>
      <StatsRow stats={stats} />
      <LogStream logs={logs} />
    </div>
  );
}
```

---

## Integration Examples

### Python script: monitor a parse in real time

Run this alongside a batch parse to see events as they arrive:

```python
import threading
from src.api.services.parse_service import start_batch_parse
from src.orchestrator.live_events import enable, subscribe, reset, STITCH_COMPLETE

def monitor():
    for event in subscribe(include_history=False):
        print(f"[{event.event_type}] {event.data}")
        if event.event_type == STITCH_COMPLETE:
            print("Stitching done.")
            return

reset()
enable()

monitor_thread = threading.Thread(target=monitor, daemon=True)
monitor_thread.start()

# Trigger parse
start_batch_parse()

monitor_thread.join(timeout=300)
```

### curl: watch SSE from terminal

```bash
curl -N http://localhost:8000/api/dashboard/live
```

The `-N` flag disables buffering so each event is printed as it arrives.

### curl: trigger a parse and watch it complete

```bash
# Trigger the parse
curl -X POST http://localhost:8000/api/parse/trigger

# In a second terminal, watch the live stream
curl -N http://localhost:8000/api/dashboard/live | grep -v heartbeat
```

### Node.js: consume SSE outside the browser

```javascript
const EventSource = require('eventsource'); // npm install eventsource

const es = new EventSource('http://localhost:8000/api/dashboard/live');

es.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'heartbeat') {
    if (data.batch_status === 'done') {
      console.log('Parse complete');
      es.close();
      process.exit(0);
    }
    return;
  }
  console.log(`[${data.level}] ${data.message}`);
};
```

### Python: consume SSE with `sseclient`

```bash
pip install sseclient-py requests
```

```python
import json
import requests
import sseclient

def watch_parse():
    response = requests.get(
        'http://localhost:8000/api/dashboard/live',
        stream=True,
        headers={'Accept': 'text/event-stream'},
    )
    client = sseclient.SSEClient(response)

    for event in client.events():
        data = json.loads(event.data)

        if data.get('type') == 'heartbeat':
            print(f"Status: {data['batch_status']}")
            if data['batch_status'] == 'done':
                print("Batch parse complete.")
                break
        else:
            level = data.get('level', 'info').upper()
            jid = data.get('jurisdiction_id') or ''
            msg = data.get('message', '')
            print(f"[{level}] [{jid}] {msg}")

watch_parse()
```
