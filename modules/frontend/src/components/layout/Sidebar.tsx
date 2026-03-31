import React from 'react';
import { Clock, Database } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { FieldSearch } from '../../features/field-search/FieldSearch';

export function Sidebar() {
  const { recentTraces, setFieldName, setSelectedFields, traceResult } = useAppStore();

  return (
    <aside
      className="w-[280px] shrink-0 flex flex-col overflow-hidden"
      style={{ background: 'var(--bg-surface)', borderRight: '1px solid var(--border)' }}
    >
      {/* Section header */}
      <div
        className="flex items-center gap-2 px-4 py-2.5 shrink-0"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <Database size={11} style={{ color: 'var(--amber)' }} />
        <span className="label-heading" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Field Tracer</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-5">
        <FieldSearch />

        {recentTraces.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Clock size={10} style={{ color: 'var(--text-muted)' }} />
              <span className="label-heading" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Recent</span>
            </div>
            <div className="flex flex-col gap-0.5">
              {recentTraces.map((f) => {
                const isActive = traceResult?.field_name === f;
                return (
                  <button
                    key={f}
                    onClick={() => { setFieldName(f); setSelectedFields([f]); }}
                    className="text-left px-2.5 py-1.5 rounded text-xs font-mono transition-all flex items-center gap-2"
                    style={{
                      color: isActive ? 'var(--amber)' : 'var(--text-secondary)',
                      background: isActive ? 'var(--amber-glow)' : 'transparent',
                      border: isActive ? '1px solid rgba(245,166,35,0.2)' : '1px solid transparent',
                    }}
                  >
                    {isActive && <span className="status-dot amber animate-pulse-amber" />}
                    {f}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Bottom status */}
      <div
        className="px-4 py-2.5 flex items-center gap-2 shrink-0"
        style={{ borderTop: '1px solid var(--border)' }}
      >
        <span className="status-dot green" />
        <span style={{ color: 'var(--text-muted)', fontSize: '10px', fontFamily: "'IBM Plex Mono', monospace" }}>
          API connected
        </span>
      </div>
    </aside>
  );
}
