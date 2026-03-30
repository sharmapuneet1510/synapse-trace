import React, { useEffect, useRef } from 'react';
import { Trash2, RefreshCw } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { traceApi } from '../../api/traceApi';

const LEVEL_STYLES: Record<string, string> = {
  ERROR: 'text-red-400',
  WARN: 'text-yellow-400',
  WARNING: 'text-yellow-400',
  INFO: 'text-blue-400',
  DEBUG: 'text-slate-500',
  TRACE: 'text-slate-600',
};

export function LogsPanel() {
  const { logs, clearLogs, addLogs } = useAppStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleRefresh = async () => {
    try {
      const recent = await traceApi.getRecentLogs();
      if (Array.isArray(recent)) addLogs(recent);
    } catch { /* ignore */ }
  };

  return (
    <div className="h-full flex flex-col bg-slate-950">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800 shrink-0">
        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          Trace Logs ({logs.length})
        </span>
        <div className="flex gap-1">
          <button onClick={handleRefresh} className="p-1 text-slate-600 hover:text-slate-400 transition-colors">
            <RefreshCw size={11} />
          </button>
          <button onClick={clearLogs} className="p-1 text-slate-600 hover:text-slate-400 transition-colors">
            <Trash2 size={11} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto font-mono">
        {logs.length === 0 ? (
          <div className="text-[10px] text-slate-600 text-center py-4">No logs yet — run a trace</div>
        ) : (
          logs.map((log, i) => {
            const levelStyle = LEVEL_STYLES[(log.level || '').toUpperCase()] || 'text-slate-500';
            return (
              <div key={i} className="flex gap-2 px-3 py-0.5 hover:bg-slate-900 border-b border-slate-900">
                <span className="text-[9px] text-slate-600 shrink-0 w-20 truncate">
                  {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '—'}
                </span>
                <span className={`text-[10px] font-semibold shrink-0 w-12 ${levelStyle}`}>
                  {(log.level || '').toUpperCase()}
                </span>
                <span className="text-[9px] text-slate-600 shrink-0 w-16 truncate">{log.module}</span>
                <span className="text-[10px] text-slate-400 truncate">{log.message}</span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
