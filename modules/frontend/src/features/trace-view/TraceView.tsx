import React from 'react';
import { useAppStore } from '../../store/appStore';
import { PipelineView } from '../pipeline-view/PipelineView';
import { BranchView } from '../branch-view/BranchView';
import { EmptyState } from '../../components/ui/EmptyState';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { GitBranch } from 'lucide-react';

export function TraceView() {
  const { traceResult, viewMode, isTracing } = useAppStore();

  if (isTracing) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-400 rounded-full animate-spin" />
          <p className="text-sm">Running trace…</p>
        </div>
      </div>
    );
  }

  if (!traceResult) {
    return (
      <EmptyState
        icon={<GitBranch size={56} />}
        title="Enter a field name to trace"
        description="SynapseTrace will scan XSLT and Java sources and visualize the complete lineage pipeline."
      />
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Summary bar */}
      <div className="shrink-0 bg-slate-900 border-b border-slate-700 px-4 py-2 flex items-center gap-3 flex-wrap">
        <span className="text-xs text-slate-500">origin:</span>
        <Badge label={traceResult.origin} />
        <span className="text-xs text-slate-500">|</span>
        <span className="text-xs text-slate-400">{traceResult.summary.total_nodes} nodes</span>
        <span className="text-xs text-slate-400">{traceResult.summary.branch_count} branches</span>
        {traceResult.summary.has_xslt && <Badge label="XSLT" />}
        {traceResult.summary.has_java && <Badge label="JAVA" />}
      </div>

      {/* Graph canvas */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'pipeline' ? <PipelineView /> : <BranchView />}
      </div>

      {/* Explanation cards */}
      <div className="shrink-0 bg-slate-900 border-t border-slate-700 p-3 grid grid-cols-2 gap-3 max-h-52 overflow-y-auto">
        <Card title="Business Explanation" className="text-xs text-slate-300 leading-relaxed">
          {traceResult.summary.business_explanation || '—'}
        </Card>
        <Card title="Technical Explanation">
          <pre className="text-[10px] text-slate-400 leading-relaxed whitespace-pre-wrap overflow-hidden max-h-36">
            {traceResult.summary.technical_explanation || '—'}
          </pre>
        </Card>
      </div>
    </div>
  );
}
