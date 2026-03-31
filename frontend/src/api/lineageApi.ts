/**
 * Lineage API client — all calls to the /api/lineage endpoints.
 *
 * Base URL is read from the VITE_API_URL env var (default: http://localhost:8000).
 */

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ScanRequest {
  field_name: string;
  project_repos: string[];
  lib_repos?: string[];
  deep_scan_packages?: string[];
  extraction?: string[];
  transformation?: string[];
  max_depth?: number;
  enable_condition_tracing?: boolean;
  enable_xslt_imports?: boolean;
}

export interface DeriveRequest {
  field_name: string;
  project_repos: string[];
  lib_repos?: string[];
  deep_scan_packages?: string[];
  prompt_name?: string;
}

export interface DeriveResponse {
  trace_id: string;
  field_name: string;
  prompt_name: string;
  derivation: string;
  model: string;
}

export interface PromptListResponse {
  prompts: string[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Lineage endpoints ─────────────────────────────────────────────────────────

/** Run a full field lineage trace. */
export async function scanField(req: ScanRequest) {
  return apiFetch('/api/lineage/scan', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/** Run a named LLM prompt against a trace. */
export async function deriveField(req: DeriveRequest): Promise<DeriveResponse> {
  return apiFetch('/api/lineage/derive', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/** List available LLM prompt names. */
export async function listPrompts(): Promise<PromptListResponse> {
  return apiFetch('/api/lineage/prompts');
}

/** List fields currently in the in-process cache. */
export async function listCache(): Promise<{ cached_fields: string[]; count: number }> {
  return apiFetch('/api/lineage/cache');
}

/** Export a trace in the requested format (html | md | json | neo4j). */
export async function exportTrace(fieldName: string, fmt: string): Promise<string> {
  const res = await fetch(`${BASE}/api/lineage/export/${fieldName}/${fmt}`);
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  return res.text();
}

// ── Chat endpoints ────────────────────────────────────────────────────────────

export async function createChatSession(title?: string, userId = 'default') {
  return apiFetch('/api/chat/sessions', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, title }),
  });
}

export async function listChatSessions(userId = 'default') {
  return apiFetch(`/api/chat/sessions?user_id=${userId}`);
}

export async function getChatSession(sessionId: string) {
  return apiFetch(`/api/chat/sessions/${sessionId}`);
}

export interface SendMessageRequest {
  content: string;
  jurisdiction_id?: string;
  field_name?: string;
}

export async function sendMessage(sessionId: string, body: SendMessageRequest) {
  return apiFetch(`/api/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function deleteChatSession(sessionId: string) {
  return apiFetch(`/api/chat/sessions/${sessionId}`, { method: 'DELETE' });
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function healthCheck(): Promise<{ status: string; service: string }> {
  return apiFetch('/api/health');
}
