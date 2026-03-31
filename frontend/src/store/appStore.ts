import { create } from 'zustand';
import type { TraceResult } from '../types/trace';
import type { TraceConfig } from '../types/config';
import {
  DUMMY_TRACE,
  DUMMY_LOGS,
  DUMMY_CHAT_SESSIONS,
  DUMMY_CHAT_MESSAGES,
  DUMMY_RECENT_TRACES,
} from '../data/dummyData';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  module: string;
  message: string;
  trace_id?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  jurisdiction_id?: string;
  field_name?: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface AppState {
  // ── Field search ───────────────────────────────────────────────────────────
  fieldName: string;
  jurisdiction: string;
  setFieldName: (v: string) => void;
  setJurisdiction: (v: string) => void;

  // ── Multi-select search controls ──────────────────────────────────────────
  selectedJurisdictions: string[];
  selectedFieldTypes: string[];
  selectedFields: string[];
  setSelectedJurisdictions: (v: string[]) => void;
  setSelectedFieldTypes: (v: string[]) => void;
  setSelectedFields: (v: string[]) => void;

  // ── Trace state ────────────────────────────────────────────────────────────
  isTracing: boolean;
  traceResult: TraceResult | null;
  traceError: string | null;
  setTracing: (v: boolean) => void;
  setTraceResult: (r: TraceResult | null) => void;
  setTraceError: (e: string | null) => void;

  // ── View mode ──────────────────────────────────────────────────────────────
  viewMode: 'pipeline' | 'branch';
  setViewMode: (m: 'pipeline' | 'branch') => void;

  // ── Selected node ──────────────────────────────────────────────────────────
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;

  // ── Config panel ───────────────────────────────────────────────────────────
  configOpen: boolean;
  setConfigOpen: (v: boolean) => void;
  config: { trace: TraceConfig } | null;
  setConfig: (c: { trace: TraceConfig }) => void;

  // ── Logs panel ─────────────────────────────────────────────────────────────
  logsOpen: boolean;
  setLogsOpen: (v: boolean) => void;
  logs: LogEntry[];
  addLogs: (entries: LogEntry[]) => void;
  clearLogs: () => void;

  // ── Chat ───────────────────────────────────────────────────────────────────
  chatOpen: boolean;
  setChatOpen: (v: boolean) => void;
  chatSessions: ChatSession[];
  activeChatSession: string | null;
  chatMessages: ChatMessage[];
  isChatLoading: boolean;
  setChatSessions: (sessions: ChatSession[]) => void;
  setActiveChatSession: (id: string | null) => void;
  setChatMessages: (messages: ChatMessage[]) => void;
  appendChatMessages: (messages: ChatMessage[]) => void;
  setChatLoading: (v: boolean) => void;

  // ── Business derivation ────────────────────────────────────────────────────
  derivationOpen: boolean;
  setDerivationOpen: (v: boolean) => void;
  derivationText: string | null;
  derivationPrompt: string;
  isDerivationLoading: boolean;
  setDerivationText: (t: string | null) => void;
  setDerivationPrompt: (p: string) => void;
  setDerivationLoading: (v: boolean) => void;

  // ── API Docs panel ─────────────────────────────────────────────────────────
  apiDocsOpen: boolean;
  setApiDocsOpen: (v: boolean) => void;

  // ── Recent traces ──────────────────────────────────────────────────────────
  recentTraces: string[];
  addRecentTrace: (fieldName: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // ── Field search ───────────────────────────────────────────────────────────
  fieldName: DUMMY_TRACE.field_name,
  jurisdiction: '',
  setFieldName: (v) => set({ fieldName: v }),
  setJurisdiction: (v) => set({ jurisdiction: v }),

  // ── Multi-select search controls ──────────────────────────────────────────
  selectedJurisdictions: ['EMIR'],
  selectedFieldTypes: ['TradeState'],
  selectedFields: ['N_CLEARED'],
  setSelectedJurisdictions: (v) => set({ selectedJurisdictions: v }),
  setSelectedFieldTypes: (v) => set({ selectedFieldTypes: v }),
  setSelectedFields: (v) => set({ selectedFields: v }),

  // ── Trace state — pre-loaded with dummy data ───────────────────────────────
  isTracing: false,
  traceResult: DUMMY_TRACE,
  traceError: null,
  setTracing: (v) => set({ isTracing: v, traceError: null, ...(v ? { traceResult: null } : {}) }),
  setTraceResult: (r) => set({ traceResult: r, traceError: null, isTracing: false }),
  setTraceError: (e) => set({ traceError: e, isTracing: false }),

  // ── View mode ──────────────────────────────────────────────────────────────
  viewMode: 'pipeline',
  setViewMode: (m) => set({ viewMode: m }),

  // ── Selected node ──────────────────────────────────────────────────────────
  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),

  // ── Config panel ───────────────────────────────────────────────────────────
  configOpen: false,
  setConfigOpen: (v) => set({ configOpen: v }),
  config: null,
  setConfig: (c) => set({ config: c }),

  // ── Logs panel — pre-loaded with dummy logs ────────────────────────────────
  logsOpen: false,
  setLogsOpen: (v) => set({ logsOpen: v }),
  logs: DUMMY_LOGS,
  addLogs: (entries) => set((s) => ({ logs: [...s.logs, ...entries].slice(-500) })),
  clearLogs: () => set({ logs: [] }),

  // ── Chat — pre-loaded with dummy sessions ──────────────────────────────────
  chatOpen: false,
  setChatOpen: (v) => set({ chatOpen: v }),
  chatSessions: DUMMY_CHAT_SESSIONS,
  activeChatSession: DUMMY_CHAT_SESSIONS[0].id,
  chatMessages: DUMMY_CHAT_MESSAGES,
  isChatLoading: false,
  setChatSessions: (sessions) => set({ chatSessions: sessions }),
  setActiveChatSession: (id) => set({ activeChatSession: id, chatMessages: [] }),
  setChatMessages: (messages) => set({ chatMessages: messages }),
  appendChatMessages: (messages) =>
    set((s) => ({ chatMessages: [...s.chatMessages, ...messages] })),
  setChatLoading: (v) => set({ isChatLoading: v }),

  // ── Business derivation ────────────────────────────────────────────────────
  derivationOpen: false,
  setDerivationOpen: (v) => set({ derivationOpen: v }),
  derivationText: null,
  derivationPrompt: 'business_derivation',
  isDerivationLoading: false,
  setDerivationText: (t) => set({ derivationText: t }),
  setDerivationPrompt: (p) => set({ derivationPrompt: p }),
  setDerivationLoading: (v) => set({ isDerivationLoading: v }),

  // ── API Docs panel ─────────────────────────────────────────────────────────
  apiDocsOpen: false,
  setApiDocsOpen: (v) => set({ apiDocsOpen: v }),

  // ── Recent traces — pre-populated ─────────────────────────────────────────
  recentTraces: DUMMY_RECENT_TRACES,
  addRecentTrace: (fieldName) =>
    set((s) => ({
      recentTraces: [fieldName, ...s.recentTraces.filter((f) => f !== fieldName)].slice(0, 10),
    })),
}));
