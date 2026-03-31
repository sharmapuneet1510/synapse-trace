import React, { useMemo } from 'react';
import { X, FileCode, Package, GitBranch, Hash, Code2 } from 'lucide-react';
import { useAppStore } from '../../store/appStore';

const TYPE_CONFIG: Record<string, { color: string; label: string }> = {
  EXTRACTION:             { color: '#a78bfa', label: 'EXTRACT' },
  MAPPING:                { color: '#22d3ee', label: 'MAP' },
  ENRICHMENT:             { color: '#10b981', label: 'ENRICH' },
  OVERRIDE:               { color: '#f59e0b', label: 'OVERRIDE' },
  DEFAULTING:             { color: '#64748b', label: 'DEFAULT' },
  PASS_THROUGH:           { color: '#475569', label: 'PASS' },
  CONDITIONAL_ASSIGNMENT: { color: '#ff6b35', label: 'CONDITIONAL' },
  FINAL_REPORT_ASSIGNMENT:{ color: '#f87171', label: 'FINAL' },
};

export function NodeDetailsPanel() {
  const { selectedNodeId, setSelectedNodeId, traceResult } = useAppStore();

  const node = useMemo(() => {
    if (!selectedNodeId || !traceResult) return null;
    const step = traceResult.pipeline.find((s) => s.step_id === selectedNodeId);
    if (step) return step;
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
  }, [selectedNodeId, traceResult]);

  if (!selectedNodeId || !node) return null;

  const ev = (node.evidence as Record<string, unknown>) || {};
  const tType = node.transformation_type || '';
  const cfg = TYPE_CONFIG[tType] || { color: 'var(--text-secondary)', label: tType };

  return (
    <aside
      className="w-[320px] shrink-0 flex flex-col overflow-hidden animate-fade-up"
      style={{ background: 'var(--bg-surface)', borderLeft: '1px solid var(--border)' }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 shrink-0"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2">
          <span className="label-heading" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>NODE DETAILS</span>
          {tType && (
            <span
              className="label-tag px-1.5 py-0.5 rounded"
              style={{ color: cfg.color, background: `${cfg.color}14`, border: `1px solid ${cfg.color}30` }}
            >
              {cfg.label}
            </span>
          )}
        </div>
        <button
          onClick={() => setSelectedNodeId(null)}
          className="flex items-center justify-center transition-all"
          style={{
            width: 22, height: 22,
            borderRadius: 3,
            color: 'var(--text-muted)',
            border: '1px solid var(--border)',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.color = 'var(--text-primary)';
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-bright)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
          }}
        >
          <X size={11} />
        </button>
      </div>

      {/* Accent bar */}
      <div style={{ height: 2, background: cfg.color, opacity: 0.6 }} />

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {/* Label */}
        <div>
          <div className="label-tag mb-1" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>LABEL</div>
          <div
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: '12px',
              fontWeight: 500,
              color: 'var(--text-primary)',
              lineHeight: 1.4,
            }}
          >
            {node.label}
          </div>
        </div>

        {/* Type badge */}
        {node.type && (
          <div className="flex items-center gap-2">
            <span className="label-tag" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>TECH</span>
            <span
              className="label-tag px-2 py-0.5 rounded"
              style={{
                color: node.type === 'xslt_template' ? 'var(--violet)' : 'var(--cyan)',
                background: node.type === 'xslt_template' ? 'rgba(167,139,250,0.1)' : 'rgba(34,211,238,0.08)',
                border: `1px solid ${node.type === 'xslt_template' ? 'rgba(167,139,250,0.25)' : 'rgba(34,211,238,0.2)'}`,
              }}
            >
              {node.type === 'xslt_template' ? 'XSLT' : node.type === 'java_method' ? 'JAVA' : node.type.toUpperCase()}
            </span>
          </div>
        )}

        {/* Divider */}
        <div style={{ height: 1, background: 'var(--border)' }} />

        {/* Metadata */}
        <div className="flex flex-col gap-2.5">
          {ev.repository && (
            <MetaRow icon={<GitBranch size={11} />} label="REPOSITORY" value={String(ev.repository)} />
          )}
          {ev.module && (
            <MetaRow icon={<Package size={11} />} label="MODULE" value={String(ev.module)} />
          )}
          {ev.package && (
            <MetaRow icon={<Package size={11} />} label="PACKAGE" value={String(ev.package)} mono />
          )}
          {ev.class_or_template && (
            <MetaRow icon={<FileCode size={11} />} label="CLASS / TEMPLATE" value={String(ev.class_or_template)} mono />
          )}
          {ev.method_or_template_name && (
            <MetaRow icon={<FileCode size={11} />} label="METHOD" value={String(ev.method_or_template_name)} mono />
          )}
          {ev.file_path && (
            <MetaRow icon={<FileCode size={11} />} label="FILE" value={String(ev.file_path)} mono truncate />
          )}
          {ev.line_number && (
            <MetaRow icon={<Hash size={11} />} label="LINE" value={String(ev.line_number)} />
          )}
          {ev.condition_text && (
            <div>
              <div className="label-tag mb-1.5 flex items-center gap-1.5" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>
                <GitBranch size={10} /> CONDITION
              </div>
              <div
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderLeft: '2px solid var(--coral)',
                  borderRadius: 4,
                  padding: '6px 8px',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: '10px',
                  color: '#fde68a',
                  lineHeight: 1.5,
                }}
              >
                {String(ev.condition_text)}
              </div>
            </div>
          )}
        </div>

        {/* Code snippet */}
        {ev.raw_code && (
          <div>
            <div className="label-tag mb-1.5 flex items-center gap-1.5" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>
              <Code2 size={10} /> CODE SNIPPET
            </div>
            <pre className="st-code" style={{ maxHeight: 160, overflowY: 'auto' }}>
              {String(ev.raw_code)}
            </pre>
          </div>
        )}
      </div>
    </aside>
  );
}

function MetaRow({
  icon, label, value, mono = false, truncate = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
  truncate?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <span style={{ color: 'var(--text-muted)', marginTop: 1, flexShrink: 0 }}>{icon}</span>
      <div className="min-w-0 flex-1">
        <div className="label-tag" style={{ color: 'var(--text-muted)', fontSize: '9px', marginBottom: 2 }}>{label}</div>
        <div
          style={{
            fontFamily: mono ? "'IBM Plex Mono', monospace" : 'inherit',
            fontSize: '11px',
            color: 'var(--text-secondary)',
            wordBreak: truncate ? undefined : 'break-all',
            overflow: truncate ? 'hidden' : undefined,
            textOverflow: truncate ? 'ellipsis' : undefined,
            whiteSpace: truncate ? 'nowrap' : undefined,
          }}
        >
          {value}
        </div>
      </div>
    </div>
  );
}
