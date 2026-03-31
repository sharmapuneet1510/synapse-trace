import React, { useEffect, useRef } from 'react';
import { Trash2, RefreshCw } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { traceApi } from '../../api/traceApi';

const LEVEL_COLORS: Record<string, string> = {
  ERROR:   '#f87171',
  WARN:    '#f59e0b',
  WARNING: '#f59e0b',
  INFO:    '#22d3ee',
  DEBUG:   '#3d5275',
  TRACE:   '#253550',
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
    <div className="h-full flex flex-col" style={{ background: 'var(--bg-base)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-1.5 shrink-0"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2">
          <div className="status-dot green" />
          <span className="label-heading" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>
            TRACE LOGS
          </span>
          <span
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: '10px',
              color: 'var(--text-muted)',
            }}
          >
            ({logs.length})
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleRefresh}
            className="flex items-center justify-center transition-colors"
            style={{ width: 22, height: 22, borderRadius: 3, color: 'var(--text-muted)' }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--amber)')}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--text-muted)')}
          >
            <RefreshCw size={10} />
          </button>
          <button
            onClick={clearLogs}
            className="flex items-center justify-center transition-colors"
            style={{ width: 22, height: 22, borderRadius: 3, color: 'var(--text-muted)' }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--red)')}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--text-muted)')}
          >
            <Trash2 size={10} />
          </button>
        </div>
      </div>

      {/* Log stream */}
      <div className="flex-1 overflow-y-auto" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
        {logs.length === 0 ? (
          <div
            style={{ fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center', padding: '14px 0' }}
          >
            No logs yet — run a trace
          </div>
        ) : (
          logs.map((log, i) => {
            const level = (log.level || '').toUpperCase();
            const color = LEVEL_COLORS[level] || 'var(--text-muted)';
            return (
              <div
                key={i}
                className="flex gap-3 px-3 py-0.5 transition-colors"
                style={{ borderBottom: '1px solid #090d1899' }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = 'var(--bg-elevated)')}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = 'transparent')}
              >
                <span style={{ fontSize: '9px', color: 'var(--text-muted)', flexShrink: 0, width: 64 }}>
                  {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '—'}
                </span>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 600,
                    color,
                    flexShrink: 0,
                    width: 40,
                    letterSpacing: '0.05em',
                  }}
                >
                  {level}
                </span>
                <span style={{ fontSize: '9px', color: 'var(--text-muted)', flexShrink: 0, width: 60, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {log.module}
                </span>
                <span style={{ fontSize: '10px', color: 'var(--text-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {log.message}
                </span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
