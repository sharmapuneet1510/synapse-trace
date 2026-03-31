import React from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

const TYPE_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  EXTRACTION:             { color: '#7c3aed', bg: 'rgba(124,58,237,0.07)',  label: 'EXTRACT' },
  MAPPING:                { color: '#0891b2', bg: 'rgba(8,145,178,0.07)',   label: 'MAP' },
  ENRICHMENT:             { color: '#059669', bg: 'rgba(5,150,105,0.07)',   label: 'ENRICH' },
  OVERRIDE:               { color: '#d97706', bg: 'rgba(217,119,6,0.07)',   label: 'OVERRIDE' },
  DEFAULTING:             { color: '#6b7280', bg: 'rgba(107,114,128,0.07)', label: 'DEFAULT' },
  PASS_THROUGH:           { color: '#9ca3af', bg: 'rgba(156,163,175,0.07)', label: 'PASS' },
  CONDITIONAL_ASSIGNMENT: { color: '#ea580c', bg: 'rgba(234,88,12,0.07)',   label: 'COND' },
  FINAL_REPORT_ASSIGNMENT:{ color: '#dc2626', bg: 'rgba(220,38,38,0.07)',   label: 'FINAL' },
};

export function PipelineNode({ data, selected }: NodeProps) {
  const tType = (data.transformation_type as string) || '';
  const cfg = TYPE_CONFIG[tType] || { color: '#3d5275', bg: 'rgba(61,82,117,0.08)', label: '—' };
  const nodeType = (data.node_type as string) || '';
  const label = (data.label as string) || '';
  const evidence = (data.evidence as Record<string, unknown>) || {};

  const techLabel = nodeType === 'xslt_template' ? 'XSLT' : nodeType === 'java_method' ? 'JAVA' : nodeType.toUpperCase();

  return (
    <div
      style={{
        background: '#ffffff',
        border: selected
          ? `1.5px solid ${cfg.color}`
          : `1px solid #e2e4e9`,
        borderLeft: `3px solid ${cfg.color}`,
        borderRadius: 5,
        minWidth: 168,
        maxWidth: 230,
        cursor: 'pointer',
        boxShadow: selected
          ? `0 0 0 3px ${cfg.color}18, 0 4px 16px rgba(0,0,0,0.1)`
          : '0 1px 4px rgba(0,0,0,0.08)',
        transition: 'all 0.15s',
        padding: 0,
        overflow: 'hidden',
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: cfg.color, width: 6, height: 6, border: 'none', left: -3 }}
      />

      {/* Top color strip */}
      <div
        style={{
          height: 2,
          background: cfg.color,
          opacity: selected ? 1 : 0.4,
        }}
      />

      {/* Body */}
      <div style={{ padding: '8px 10px 8px 10px' }}>
        {/* Type badge row */}
        <div className="flex items-center justify-between mb-1.5">
          <span
            className="label-tag px-1.5 py-0.5 rounded"
            style={{ color: cfg.color, background: cfg.bg, fontSize: '9px' }}
          >
            {cfg.label}
          </span>
          <span
            className="label-tag"
            style={{ color: '#9ca3af', fontSize: '9px' }}
          >
            {techLabel}
          </span>
        </div>

        {/* Label */}
        <div
          style={{
            color: selected ? '#111827' : '#374151',
            fontSize: '11px',
            fontWeight: 500,
            lineHeight: 1.35,
            wordBreak: 'break-word',
            fontFamily: "'IBM Plex Mono', monospace",
          }}
        >
          {label}
        </div>

        {/* Evidence */}
        {evidence.class_or_template && (
          <div
            className="mt-1.5 truncate"
            style={{ color: '#9ca3af', fontSize: '9px', fontFamily: "'IBM Plex Mono', monospace" }}
          >
            {String(evidence.class_or_template)}
            {evidence.method_or_template_name ? `.${String(evidence.method_or_template_name)}()` : ''}
          </div>
        )}

        {evidence.line_number && (
          <div style={{ color: '#d1d5db', fontSize: '9px', marginTop: 2 }}>
            :{String(evidence.line_number)}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: cfg.color, width: 6, height: 6, border: 'none', right: -3 }}
      />
    </div>
  );
}
