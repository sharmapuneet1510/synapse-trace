import React from 'react';
import { Clock } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { FieldSearch } from '../../features/field-search/FieldSearch';

export function Sidebar() {
  const { recentTraces, setFieldName, traceResult } = useAppStore();

  return (
    <aside className="w-[280px] shrink-0 bg-slate-900 border-r border-slate-700 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        <FieldSearch />

        {/* Recent traces */}
        {recentTraces.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Clock size={12} className="text-slate-500" />
              <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Recent</span>
            </div>
            <div className="flex flex-col gap-1">
              {recentTraces.map((f) => (
                <button
                  key={f}
                  onClick={() => setFieldName(f)}
                  className={`text-left px-2 py-1.5 rounded text-xs font-mono transition-colors ${
                    traceResult?.field_name === f
                      ? 'bg-blue-900/40 text-blue-300'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
