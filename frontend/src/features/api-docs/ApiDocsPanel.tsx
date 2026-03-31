import React, { useState } from 'react';
import { BookOpen, X, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { useAppStore } from '../../store/appStore';

interface Endpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  summary: string;
  description: string;
  request?: string;
  response: string;
}

interface ApiGroup {
  name: string;
  color: string;
  endpoints: Endpoint[];
}

const METHOD_COLORS: Record<string, string> = {
  GET:    '#10b981',
  POST:   '#f5a623',
  PUT:    '#22d3ee',
  DELETE: '#f87171',
};

const API_GROUPS: ApiGroup[] = [
  {
    name: 'Lineage',
    color: '#f5a623',
    endpoints: [
      {
        method: 'POST', path: '/api/lineage/scan',
        summary: 'Trace a field through XSLT + Java',
        description: 'Scans repositories, detects origins, follows the call chain. Result is cached by field name.',
        request: JSON.stringify({ field_name: 'N_CLEARED', project_repos: ['./project'], lib_repos: ['./lib'], deep_scan_packages: ['com.corp.*'], max_depth: 20 }, null, 2),
        response: JSON.stringify({ trace_id: 'uuid', field_name: 'N_CLEARED', summary: { origin: 'XSLT_THEN_JAVA', total_nodes: 9, branch_count: 4 }, nodes: [], edges: [], branches: [] }, null, 2),
      },
      {
        method: 'POST', path: '/api/lineage/derive',
        summary: 'Run LLM prompt on a trace',
        description: 'Renders a Jinja2 prompt with trace context and passes it to the LLM stub. Supports custom_prompt for ad-hoc Jinja2 templates.',
        request: JSON.stringify({ field_name: 'N_CLEARED', project_repos: [], prompt_name: 'business_derivation', custom_prompt: null }, null, 2),
        response: JSON.stringify({ trace_id: 'uuid', field_name: 'N_CLEARED', prompt_name: 'business_derivation', derivation: '[LLM Stub] …', model: 'stub' }, null, 2),
      },
      {
        method: 'GET', path: '/api/lineage/export/{field_name}/{fmt}',
        summary: 'Export trace as HTML, MD, JSON or Neo4j',
        description: 'Formats: html, md, json, neo4j. Requires field to have been scanned first.',
        response: '<!-- HTML report -->\n<html>...</html>',
      },
      {
        method: 'GET', path: '/api/lineage/prompts',
        summary: 'List available LLM prompt templates',
        description: 'Returns all registered Jinja2 template names.',
        response: JSON.stringify({ prompts: ['business_derivation', 'technical_summary', 'field_impact', 'chat_context'] }, null, 2),
      },
      {
        method: 'GET', path: '/api/lineage/cache',
        summary: 'List cached field names',
        description: 'Returns fields currently held in the in-process result cache.',
        response: JSON.stringify({ cached_fields: ['N_CLEARED', 'TRADE_STATUS'], count: 2 }, null, 2),
      },
      {
        method: 'DELETE', path: '/api/lineage/cache/{field_name}',
        summary: 'Evict a field from the cache',
        description: 'Removes cached result, forcing a fresh scan next time.',
        response: JSON.stringify({ evicted: 'N_CLEARED' }, null, 2),
      },
    ],
  },
  {
    name: 'Chat',
    color: '#10b981',
    endpoints: [
      {
        method: 'POST', path: '/api/chat/sessions',
        summary: 'Create a chat session',
        description: 'Creates a new MSSQL-backed chat session.',
        response: JSON.stringify({ id: 'sess-uuid', title: null, created_at: '2026-03-31T09:00:00Z', message_count: 0 }, null, 2),
      },
      {
        method: 'GET', path: '/api/chat/sessions',
        summary: 'List all chat sessions',
        description: 'Returns sessions ordered by updated_at desc.',
        response: JSON.stringify([{ id: 'sess-uuid', title: 'N_CLEARED clearing logic', updated_at: '2026-03-31T09:05:00Z', message_count: 4 }], null, 2),
      },
      {
        method: 'POST', path: '/api/chat/sessions/{session_id}/messages',
        summary: 'Send a message',
        description: 'Sends user message and returns [user_msg, assistant_msg]. Context: field_name, jurisdiction_id.',
        request: JSON.stringify({ content: 'What triggers N_CLEARED=Y?', field_name: 'N_CLEARED' }, null, 2),
        response: JSON.stringify([{ role: 'user', content: 'What triggers N_CLEARED=Y?' }, { role: 'assistant', content: '[LLM Stub] …' }], null, 2),
      },
      {
        method: 'DELETE', path: '/api/chat/sessions/{session_id}',
        summary: 'Delete a session',
        description: 'Deletes session and all its messages.',
        response: JSON.stringify({ deleted: 'sess-uuid' }, null, 2),
      },
    ],
  },
  {
    name: 'Health',
    color: '#22d3ee',
    endpoints: [
      {
        method: 'GET', path: '/api/health',
        summary: 'Health check',
        description: 'Returns service status, version, and DB connectivity.',
        response: JSON.stringify({ status: 'ok', version: '1.0.0', db: 'connected' }, null, 2),
      },
    ],
  },
];

export function ApiDocsPanel() {
  const { apiDocsOpen, setApiDocsOpen } = useAppStore();
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['Lineage']));

  if (!apiDocsOpen) return null;

  const toggleGroup = (name: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  return (
    <div className="st-panel animate-panel" style={{ width: 640 }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 shrink-0"
        style={{ height: 48, borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2.5">
          <div
            style={{
              width: 28, height: 28,
              background: 'rgba(167,139,250,0.1)',
              border: '1px solid rgba(167,139,250,0.25)',
              borderRadius: 4,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <BookOpen size={13} style={{ color: '#a78bfa' }} />
          </div>
          <span className="label-heading" style={{ color: 'var(--text-primary)', fontSize: '11px' }}>
            API REFERENCE
          </span>
        </div>
        <PanelCloseBtn onClick={() => setApiDocsOpen(false)} />
      </div>

      {/* Violet accent */}
      <div style={{ height: 1.5, background: '#a78bfa', opacity: 0.5 }} />

      {/* Integration info strip */}
      <div
        className="px-4 py-3 shrink-0"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-elevated)' }}
      >
        <span className="label-tag" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>BASE URL</span>
        <code
          style={{
            display: 'block',
            marginTop: 4,
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: '11px',
            color: '#a78bfa',
          }}
        >
          http://localhost:8000
        </code>
        <p style={{ marginTop: 6, fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          All endpoints return JSON. Set{' '}
          <code style={{ color: 'var(--amber)', fontSize: '10px' }}>Content-Type: application/json</code>{' '}
          for POST requests.
        </p>
      </div>

      {/* Endpoint groups */}
      <div className="flex-1 overflow-y-auto">
        {API_GROUPS.map((group) => {
          const isOpen = expanded.has(group.name);
          return (
            <div key={group.name} style={{ borderBottom: '1px solid var(--border)' }}>
              {/* Group header */}
              <button
                onClick={() => toggleGroup(group.name)}
                className="w-full flex items-center justify-between px-4 py-3 transition-all"
                style={{ background: isOpen ? 'var(--bg-elevated)' : 'transparent' }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="status-dot"
                    style={{ background: group.color, boxShadow: `0 0 5px ${group.color}` }}
                  />
                  <span
                    className="label-heading"
                    style={{ color: group.color, fontSize: '11px' }}
                  >
                    {group.name.toUpperCase()}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                    ({group.endpoints.length})
                  </span>
                </div>
                {isOpen
                  ? <ChevronDown size={12} style={{ color: 'var(--text-muted)' }} />
                  : <ChevronRight size={12} style={{ color: 'var(--text-muted)' }} />
                }
              </button>

              {/* Endpoints */}
              {isOpen && group.endpoints.map((ep) => (
                <EndpointCard key={ep.path + ep.method} endpoint={ep} groupColor={group.color} />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function EndpointCard({ endpoint, groupColor }: { endpoint: Endpoint; groupColor: string }) {
  const [open, setOpen] = useState(false);
  const [copiedReq, setCopiedReq] = useState(false);
  const [copiedRes, setCopiedRes] = useState(false);

  const methodColor = METHOD_COLORS[endpoint.method] || 'var(--text-secondary)';

  const copy = (text: string, setter: (v: boolean) => void) => {
    navigator.clipboard.writeText(text).then(() => {
      setter(true);
      setTimeout(() => setter(false), 2000);
    });
  };

  return (
    <div
      style={{
        borderTop: '1px solid var(--border)',
        background: open ? 'rgba(0,0,0,0.2)' : 'transparent',
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-all"
      >
        <span
          className="label-tag shrink-0"
          style={{
            color: methodColor,
            background: `${methodColor}14`,
            border: `1px solid ${methodColor}30`,
            padding: '2px 6px',
            borderRadius: 3,
            width: 46,
            textAlign: 'center',
            fontSize: '9px',
          }}
        >
          {endpoint.method}
        </span>
        <code
          style={{
            flex: 1,
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: '11px',
            color: open ? 'var(--text-primary)' : 'var(--text-secondary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {endpoint.path}
        </code>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)', flexShrink: 0 }}>
          {endpoint.summary}
        </span>
        {open
          ? <ChevronDown size={10} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          : <ChevronRight size={10} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        }
      </button>

      {open && (
        <div className="px-4 pb-4 flex flex-col gap-3">
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.6, marginLeft: 58 }}>
            {endpoint.description}
          </p>

          {endpoint.request && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="label-tag" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>REQUEST BODY</span>
                <CopyBtn copied={copiedReq} onClick={() => copy(endpoint.request!, setCopiedReq)} />
              </div>
              <pre
                style={{
                  background: 'var(--bg-base)',
                  border: '1px solid var(--border)',
                  borderLeft: `2px solid ${methodColor}`,
                  borderRadius: 4,
                  padding: '10px 12px',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: '10px',
                  color: '#a78bfa',
                  overflowX: 'auto',
                  margin: 0,
                  lineHeight: 1.6,
                }}
              >
                {endpoint.request}
              </pre>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="label-tag" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>RESPONSE</span>
              <CopyBtn copied={copiedRes} onClick={() => copy(endpoint.response, setCopiedRes)} />
            </div>
            <pre
              style={{
                background: 'var(--bg-base)',
                border: '1px solid var(--border)',
                borderLeft: `2px solid ${groupColor}`,
                borderRadius: 4,
                padding: '10px 12px',
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: '10px',
                color: '#10b981',
                overflowX: 'auto',
                margin: 0,
                lineHeight: 1.6,
              }}
            >
              {endpoint.response}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function CopyBtn({ copied, onClick }: { copied: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 transition-all"
      style={{
        padding: '3px 8px',
        borderRadius: 3,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-bright)',
        color: copied ? 'var(--emerald)' : 'var(--text-muted)',
        fontSize: '9px',
        fontFamily: "'Barlow Condensed', sans-serif",
        fontWeight: 600,
        letterSpacing: '0.08em',
        cursor: 'pointer',
      }}
    >
      {copied ? <Check size={9} /> : <Copy size={9} />}
      {copied ? 'COPIED' : 'COPY'}
    </button>
  );
}

function PanelCloseBtn({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center justify-center"
      style={{
        width: 26, height: 26, borderRadius: 4,
        color: 'var(--text-muted)',
        border: '1px solid var(--border)',
        background: 'transparent',
        cursor: 'pointer',
      }}
    >
      <X size={12} />
    </button>
  );
}
