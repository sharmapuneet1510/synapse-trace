import React from 'react';
import { GitBranch, Layers, Network, Settings, ScrollText } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { Badge } from '../ui/Badge';

export function Header() {
  const { traceResult, viewMode, setViewMode, setConfigOpen, setLogsOpen, logsOpen } = useAppStore();

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-700 flex items-center px-4 gap-4 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 min-w-[200px]">
        <GitBranch size={18} className="text-blue-400" />
        <span className="text-sm font-bold text-slate-100">SynapseTrace</span>
        <span className="text-xs text-slate-500 hidden sm:block">Data Lineage</span>
      </div>

      {/* Field info */}
      {traceResult && (
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-xs text-slate-500">field:</span>
          <span className="text-sm font-semibold text-blue-300 truncate">{traceResult.field_name}</span>
          <Badge label={traceResult.origin} />
          <span className="text-xs text-slate-500">{traceResult.summary.total_nodes} nodes</span>
          <span className="text-xs text-slate-500">{traceResult.summary.branch_count} branches</span>
        </div>
      )}

      <div className="flex-1" />

      {/* View toggle */}
      {traceResult && (
        <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700">
          <button
            onClick={() => setViewMode('pipeline')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              viewMode === 'pipeline' ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers size={12} /> Pipeline
          </button>
          <button
            onClick={() => setViewMode('branch')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              viewMode === 'branch' ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network size={12} /> Branch
          </button>
        </div>
      )}

      {/* Toolbar */}
      <button
        onClick={() => setLogsOpen(!logsOpen)}
        className="p-2 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
        title="Toggle logs"
      >
        <ScrollText size={16} />
      </button>
      <button
        onClick={() => setConfigOpen(true)}
        className="p-2 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
        title="Configuration"
      >
        <Settings size={16} />
      </button>
    </header>
  );
}
