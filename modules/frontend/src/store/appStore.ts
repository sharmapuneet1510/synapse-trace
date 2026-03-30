import { create } from 'zustand';
import type { TraceResult } from '../types/trace';
import type { TraceConfig } from '../types/config';

interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  module: string;
  message: string;
  trace_id?: string;
}

interface AppState {
  // Field search inputs
  fieldName: string;
  jurisdiction: string;
  setFieldName: (v: string) => void;
  setJurisdiction: (v: string) => void;

  // Trace state
  isTracing: boolean;
  traceResult: TraceResult | null;
  traceError: string | null;
  setTracing: (v: boolean) => void;
  setTraceResult: (r: TraceResult | null) => void;
  setTraceError: (e: string | null) => void;

  // View mode: pipeline vs branch
  viewMode: 'pipeline' | 'branch';
  setViewMode: (m: 'pipeline' | 'branch') => void;

  // Selected node (for details panel)
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;

  // Config panel
  configOpen: boolean;
  setConfigOpen: (v: boolean) => void;
  config: { trace: TraceConfig } | null;
  setConfig: (c: { trace: TraceConfig }) => void;

  // Logs panel
  logsOpen: boolean;
  setLogsOpen: (v: boolean) => void;
  logs: LogEntry[];
  addLogs: (entries: LogEntry[]) => void;
  clearLogs: () => void;

  // Recent traces
  recentTraces: string[];
  addRecentTrace: (fieldName: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  fieldName: '',
  jurisdiction: '',
  setFieldName: (v) => set({ fieldName: v }),
  setJurisdiction: (v) => set({ jurisdiction: v }),

  isTracing: false,
  traceResult: null,
  traceError: null,
  setTracing: (v) => set({ isTracing: v, traceError: null }),
  setTraceResult: (r) => set({ traceResult: r, traceError: null, isTracing: false }),
  setTraceError: (e) => set({ traceError: e, isTracing: false }),

  viewMode: 'pipeline',
  setViewMode: (m) => set({ viewMode: m }),

  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),

  configOpen: false,
  setConfigOpen: (v) => set({ configOpen: v }),
  config: null,
  setConfig: (c) => set({ config: c }),

  logsOpen: false,
  setLogsOpen: (v) => set({ logsOpen: v }),
  logs: [],
  addLogs: (entries) => set((s) => ({ logs: [...s.logs, ...entries].slice(-500) })),
  clearLogs: () => set({ logs: [] }),

  recentTraces: [],
  addRecentTrace: (fieldName) =>
    set((s) => ({
      recentTraces: [fieldName, ...s.recentTraces.filter((f) => f !== fieldName)].slice(0, 10),
    })),
}));
