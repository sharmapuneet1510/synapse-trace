import React from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Badge } from '../../components/ui/Badge';
import type { TransformationType } from '../../types/trace';

const BORDER_COLORS: Record<string, string> = {
  EXTRACTION: '#3b82f6',
  MAPPING: '#8b5cf6',
  ENRICHMENT: '#10b981',
  OVERRIDE: '#f59e0b',
  DEFAULTING: '#6b7280',
  PASS_THROUGH: '#94a3b8',
  CONDITIONAL_ASSIGNMENT: '#eab308',
  FINAL_REPORT_ASSIGNMENT: '#ef4444',
};

export function PipelineNode({ data, selected }: NodeProps) {
  const tType = (data.transformation_type as string) || '';
  const borderColor = BORDER_COLORS[tType] || '#475569';
  const nodeType = (data.node_type as string) || '';
  const label = (data.label as string) || '';
  const evidence = (data.evidence as Record<string, unknown>) || {};

  return (
    <div
      style={{ borderColor, borderWidth: selected ? 2 : 1.5 }}
      className="bg-slate-800 rounded-lg px-3 py-2 min-w-[160px] max-w-[220px] border cursor-pointer shadow-lg"
    >
      <Handle type="target" position={Position.Left} className="!bg-slate-600 !w-2 !h-2 !border-slate-500" />

      <div className="flex items-start justify-between gap-1 mb-1">
        <span className="text-[11px] font-semibold text-slate-100 leading-tight break-words">{label}</span>
        <span className="text-[9px] text-slate-500 shrink-0 mt-0.5">
          {nodeType === 'xslt_template' ? 'XSLT' : nodeType === 'java_method' ? 'Java' : nodeType}
        </span>
      </div>

      {tType && <Badge label={tType} className="mb-1" />}

      {evidence.class_or_template && (
        <div className="text-[10px] text-slate-500 truncate mt-1">
          {String(evidence.class_or_template)}
          {evidence.method_or_template_name ? `.${String(evidence.method_or_template_name)}()` : ''}
        </div>
      )}

      <Handle type="source" position={Position.Right} className="!bg-slate-600 !w-2 !h-2 !border-slate-500" />
    </div>
  );
}
