import React, { useState } from 'react';
import { Search, Zap } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { traceApi } from '../../api/traceApi';
import { Spinner } from '../../components/ui/Spinner';

export function FieldSearch() {
  const {
    fieldName, setFieldName,
    jurisdiction, setJurisdiction,
    isTracing, setTracing,
    setTraceResult, setTraceError,
    addRecentTrace, addLogs,
  } = useAppStore();

  const [localField, setLocalField] = useState(fieldName);
  const [localJurisdiction, setLocalJurisdiction] = useState(jurisdiction);

  const handleTrace = async () => {
    const field = localField.trim();
    if (!field) return;

    setFieldName(field);
    setJurisdiction(localJurisdiction);
    setTracing(true);

    try {
      const result = await traceApi.traceField({
        field_name: field,
        jurisdiction: localJurisdiction || undefined,
        max_depth: 20,
        enable_condition_tracing: true,
        enable_xslt_imports: true,
      });
      setTraceResult(result);
      addRecentTrace(field);

      // Fetch and add logs
      try {
        const logs = await traceApi.getLogs(result.trace_id);
        if (Array.isArray(logs)) addLogs(logs);
      } catch { /* logs are optional */ }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Trace failed';
      setTraceError(msg);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleTrace();
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold flex items-center gap-1.5">
        <Search size={11} /> Field Trace
      </div>

      <div className="flex flex-col gap-2">
        <div className="relative">
          <input
            type="text"
            value={localField}
            onChange={(e) => setLocalField(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. N_CLEARED"
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-slate-100 placeholder-slate-500
                       focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
          />
        </div>

        <input
          type="text"
          value={localJurisdiction}
          onChange={(e) => setLocalJurisdiction(e.target.value)}
          placeholder="Jurisdiction (optional)"
          className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-500
                     focus:outline-none focus:border-blue-500 font-mono"
        />

        <button
          onClick={handleTrace}
          disabled={isTracing || !localField.trim()}
          className="flex items-center justify-center gap-2 w-full py-2 px-4 rounded bg-blue-600 hover:bg-blue-500
                     disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed
                     text-white text-sm font-semibold transition-colors"
        >
          {isTracing ? (
            <><Spinner size="sm" /> Tracing…</>
          ) : (
            <><Zap size={14} /> Trace Field</>
          )}
        </button>
      </div>

      {useAppStore.getState().traceError && (
        <div className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded p-2">
          {useAppStore.getState().traceError}
        </div>
      )}
    </div>
  );
}
