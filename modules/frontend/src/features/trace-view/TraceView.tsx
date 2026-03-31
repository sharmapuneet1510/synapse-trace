import React from 'react';
import { useAppStore } from '../../store/appStore';
import { PipelineView } from '../pipeline-view/PipelineView';
import { BranchView } from '../branch-view/BranchView';
import { Activity, GitBranch, Code2, Cpu } from 'lucide-react';

const ORIGIN_COLOR: Record<string, string> = {
  XSLT_THEN_JAVA: 'var(--amber)',
  XSLT: 'var(--violet)',
  JAVA: 'var(--cyan)',
  UNKNOWN: 'var(--text-muted)',
};

export function TraceView() {
  const { traceResult, viewMode, isTracing } = useAppStore();

  if (isTracing) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-6"
        style={{ color: 'var(--text-muted)' }}>
        <div style={{ position: 'relative', width: 48, height: 48 }}>
          <div
            style={{
              width: 48, height: 48,
              border: '1.5px solid var(--border-bright)',
              borderTopColor: 'var(--amber)',
              borderRadius: '50%',
            }}
            className="animate-spin"
          />
          <Activity
            size={16}
            style={{
              color: 'var(--amber)',
              position: 'absolute',
              top: '50%', left: '50%',
              transform: 'translate(-50%, -50%)',
            }}
          />
        </div>
        <div className="flex flex-col items-center gap-1">
          <span className="label-heading" style={{ color: 'var(--amber)', fontSize: '12px' }}>
            SCANNING LINEAGE
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Parsing XSLT templates and Java call chains…
          </span>
        </div>
        {/* Fake progress steps */}
        <div className="flex flex-col gap-1.5" style={{ width: 260 }}>
          {['Loading repositories', 'Parsing XSLT sources', 'Tracing Java methods', 'Building graph'].map((step, i) => (
            <div key={step} className="flex items-center gap-2"
              style={{ animationDelay: `${i * 0.3}s` }}>
              <div className="status-dot amber animate-pulse-amber" style={{ animationDelay: `${i * 0.4}s` }} />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: "'IBM Plex Mono', monospace" }}>
                {step}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!traceResult) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-8"
        style={{ color: 'var(--text-muted)' }}>
        {/* ASCII-art style logo */}
        <div style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: '11px',
          color: 'var(--border-bright)',
          lineHeight: 1.5,
          letterSpacing: '0.05em',
          textAlign: 'center',
          userSelect: 'none',
        }}>
          <div>┌──── SYNAPSE<span style={{ color: 'var(--amber-dim)' }}>TRACE</span> ────┐</div>
          <div>│  Data Lineage Engine  │</div>
          <div>│  XSLT + Java Scanner  │</div>
          <div>└───────────────────────┘</div>
        </div>

        <div className="flex flex-col items-center gap-2">
          <span
            className="label-heading"
            style={{ color: 'var(--text-secondary)', fontSize: '13px' }}
          >
            ENTER A FIELD NAME TO TRACE
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', maxWidth: 360 }}>
            SynapseTrace scans XSLT templates and Java source code to visualize
            the complete data lineage pipeline for any output field.
          </span>
        </div>

        <div className="flex items-center gap-6">
          {[
            { icon: <Code2 size={14} />, label: 'XSLT Templates' },
            { icon: <Cpu size={14} />, label: 'Java Methods' },
            { icon: <GitBranch size={14} />, label: 'Branch Conditions' },
            { icon: <Activity size={14} />, label: 'LLM Analysis' },
          ].map(({ icon, label }) => (
            <div key={label} className="flex flex-col items-center gap-1.5">
              <div
                style={{
                  width: 36, height: 36,
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 5,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--text-muted)',
                }}
              >
                {icon}
              </div>
              <span className="label-tag" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const originColor = ORIGIN_COLOR[traceResult.origin] || 'var(--text-muted)';

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Summary strip */}
      <div
        className="shrink-0 flex items-center gap-4 px-4 py-2 flex-wrap"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}
      >
        <div className="flex items-center gap-1.5">
          <span className="label-tag" style={{ color: 'var(--text-muted)' }}>ORIGIN</span>
          <span className="label-tag px-1.5 py-0.5 rounded"
            style={{ color: originColor, background: `${originColor}14`, border: `1px solid ${originColor}30` }}>
            {traceResult.origin}
          </span>
        </div>

        <div style={{ width: 1, height: 14, background: 'var(--border-bright)' }} />

        <StatPill label="NODES" value={String(traceResult.summary.total_nodes)} />
        <StatPill label="BRANCHES" value={String(traceResult.summary.branch_count)} />

        {traceResult.summary.has_xslt && (
          <StatPill label="XSLT" value="YES" color="var(--violet)" />
        )}
        {traceResult.summary.has_java && (
          <StatPill label="JAVA" value="YES" color="var(--cyan)" />
        )}

        {(traceResult.metadata as any)?.scan_duration_ms && (
          <>
            <div style={{ width: 1, height: 14, background: 'var(--border-bright)' }} />
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: "'IBM Plex Mono', monospace" }}>
              {(traceResult.metadata as any).scan_duration_ms}ms
            </span>
          </>
        )}
      </div>

      {/* Graph canvas */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'pipeline' ? <PipelineView /> : <BranchView />}
      </div>

      {/* Explanation cards */}
      <div
        className="shrink-0 grid grid-cols-2 gap-3 p-3"
        style={{ borderTop: '1px solid var(--border)', background: 'var(--bg-surface)', maxHeight: 160 }}
      >
        <ExplainCard title="BUSINESS CONTEXT" color="var(--amber)">
          {traceResult.summary.business_explanation || '—'}
        </ExplainCard>
        <ExplainCard title="TECHNICAL SUMMARY" color="var(--cyan)">
          {traceResult.summary.technical_explanation || '—'}
        </ExplainCard>
      </div>
    </div>
  );
}

function StatPill({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="label-tag" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>{label}</span>
      <span
        style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: '11px',
          fontWeight: 500,
          color: color || 'var(--text-secondary)',
        }}
      >
        {value}
      </span>
    </div>
  );
}

function ExplainCard({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  return (
    <div
      className="flex flex-col gap-1.5 overflow-hidden"
      style={{
        background: 'var(--bg-elevated)',
        border: `1px solid var(--border)`,
        borderTop: `2px solid ${color}`,
        borderRadius: 5,
        padding: '8px 10px',
      }}
    >
      <span className="label-heading" style={{ color, fontSize: '9px' }}>{title}</span>
      <p
        style={{
          fontSize: '11px',
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
          margin: 0,
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 4,
          WebkitBoxOrient: 'vertical',
          fontFamily: "'IBM Plex Mono', monospace",
        }}
      >
        {children}
      </p>
    </div>
  );
}
