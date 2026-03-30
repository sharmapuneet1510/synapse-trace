import React, { useMemo } from 'react';
import { X, FileCode, Package, GitBranch, Hash } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { Badge } from '../../components/ui/Badge';

export function NodeDetailsPanel() {
  const { selectedNodeId, setSelectedNodeId, traceResult } = useAppStore();

  const node = useMemo(() => {
    if (!selectedNodeId || !traceResult) return null;
    return traceResult.pipeline.find((s) => s.step_id === selectedNodeId)
      || (() => {
        // Also search graph nodes
        const graphNode = traceResult.graph_json?.nodes?.find((n) => n.id === selectedNodeId);
        if (!graphNode) return null;
        return {
          step_id: graphNode.id,
          label: graphNode.label,
          type: graphNode.type,
          transformation_type: graphNode.properties?.transformation_type as string,
          evidence: graphNode.properties?.evidence as Record<string, unknown> || {},
          order: 0,
        };
      })();
  }, [selectedNodeId, traceResult]);

  if (!selectedNodeId || !node) return null;

  const ev = node.evidence as Record<string, unknown> || {};

  return (
    <aside className="w-[340px] shrink-0 bg-slate-900 border-l border-slate-700 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 shrink-0">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Node Details</span>
        <button
          onClick={() => setSelectedNodeId(null)}
          className="text-slate-500 hover:text-slate-300 transition-colors"
        >
          <X size={14} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {/* Label & type */}
        <div>
          <h3 className="text-sm font-semibold text-slate-100 leading-tight mb-2">{node.label}</h3>
          <div className="flex gap-2 flex-wrap">
            {node.transformation_type && <Badge label={node.transformation_type} />}
            {node.type && <Badge label={node.type} />}
          </div>
        </div>

        {/* Evidence metadata */}
        <div className="flex flex-col gap-2">
          {ev.repository && <MetaRow icon={<GitBranch size={11} />} label="Repository" value={String(ev.repository)} />}
          {ev.module && <MetaRow icon={<Package size={11} />} label="Module" value={String(ev.module)} />}
          {ev.package && <MetaRow icon={<Package size={11} />} label="Package" value={String(ev.package)} />}
          {ev.class_or_template && <MetaRow icon={<FileCode size={11} />} label="Class/Template" value={String(ev.class_or_template)} />}
          {ev.method_or_template_name && <MetaRow icon={<FileCode size={11} />} label="Method/Template" value={String(ev.method_or_template_name)} />}
          {ev.file_path && <MetaRow icon={<FileCode size={11} />} label="File" value={String(ev.file_path)} mono />}
          {ev.line_number && <MetaRow icon={<Hash size={11} />} label="Line" value={String(ev.line_number)} />}
          {ev.condition_text && <MetaRow icon={<GitBranch size={11} />} label="Condition" value={String(ev.condition_text)} mono />}
        </div>

        {/* Raw code */}
        {ev.raw_code && (
          <div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">Code Snippet</div>
            <pre className="text-[10px] text-emerald-300 bg-slate-950 border border-slate-700 rounded p-2.5 overflow-x-auto leading-relaxed whitespace-pre-wrap max-h-48">
              {String(ev.raw_code)}
            </pre>
          </div>
        )}
      </div>
    </aside>
  );
}

function MetaRow({
  icon, label, value, mono = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-slate-500 mt-0.5 shrink-0">{icon}</span>
      <div className="min-w-0">
        <div className="text-[10px] text-slate-500">{label}</div>
        <div className={`text-xs text-slate-300 break-all ${mono ? 'font-mono' : ''}`}>{value}</div>
      </div>
    </div>
  );
}
