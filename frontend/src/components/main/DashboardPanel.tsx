import { useState } from 'react';
import { useDashboardStats, useParseLogs, useNodes, useEdges } from '../../hooks/useDashboard';
import { triggerParse } from '../../api/dashboard';

const STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  ready: { bg: '#ecfdf5', text: '#059669' },
  done: { bg: '#ecfdf5', text: '#059669' },
  parsing: { bg: '#fffbeb', text: '#d97706' },
  running: { bg: '#fffbeb', text: '#d97706' },
  error: { bg: '#fef2f2', text: '#dc2626' },
  idle: { bg: '#f3f4f6', text: '#6b7280' },
  pending: { bg: '#f3f4f6', text: '#6b7280' },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.idle;
  return (
    <span
      className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide"
      style={{ background: s.bg, color: s.text }}
    >
      {status}
    </span>
  );
}

const LOG_COLORS: Record<string, string> = {
  error: '#dc2626',
  warn: '#d97706',
  info: '#2563eb',
  debug: '#9ca3af',
};

type DashboardTab = 'overview' | 'logs' | 'nodes' | 'edges';

export default function DashboardPanel() {
  const { data: stats } = useDashboardStats();
  const { data: logs } = useParseLogs(200);
  const [selectedJ, setSelectedJ] = useState<string | null>(null);
  const [tab, setTab] = useState<DashboardTab>('overview');
  const { data: nodesData } = useNodes(tab === 'nodes' ? selectedJ : null);
  const { data: edgesData } = useEdges(tab === 'edges' ? selectedJ : null);
  const [busy, setBusy] = useState(false);

  const handleTrigger = async () => {
    setBusy(true);
    try { await triggerParse(); } finally { setBusy(false); }
  };

  const STAT_CARDS = [
    { label: 'Jurisdictions', value: stats?.jurisdictions?.length || 0, color: '#b91c1c' },
    { label: 'Java Findings', value: stats?.totals.java_findings || 0, color: '#f97316' },
    { label: 'XSLT Findings', value: stats?.totals.xslt_findings || 0, color: '#2563eb' },
    { label: 'Nodes', value: stats?.totals.nodes || 0, color: '#059669' },
    { label: 'Edges', value: stats?.totals.edges || 0, color: '#7c3aed' },
  ];

  return (
    <div className="p-6 pb-12 max-w-[1200px]">
      {/* Top */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-[20px] font-bold text-gray-900 tracking-[-0.02em]">Dashboard</h2>
          <div className="flex items-center gap-2 mt-1 text-[12px] text-gray-500">
            <span>Batch:</span>
            <StatusBadge status={stats?.batch_status || 'idle'} />
            {stats?.batch_started && (
              <span className="text-gray-400">
                Started {new Date(stats.batch_started).toLocaleTimeString()}
              </span>
            )}
            {stats?.batch_completed && (
              <span className="text-gray-400">
                &middot; Done {new Date(stats.batch_completed).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleTrigger}
          disabled={busy || stats?.batch_status === 'running'}
          className="px-5 py-2.5 text-white text-[13px] font-semibold rounded-lg transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg"
          style={{
            background: 'linear-gradient(135deg, #b91c1c, #991b1b)',
            boxShadow: '0 2px 8px rgba(185,28,28,0.25)',
          }}
        >
          {stats?.batch_status === 'running' ? 'Parsing...' : 'Trigger Batch Parse'}
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-5 gap-3 mb-6">
        {STAT_CARDS.map((c) => (
          <div
            key={c.label}
            className="bg-white rounded-lg border border-gray-200 p-4"
            style={{ borderLeft: `4px solid ${c.color}` }}
          >
            <div className="text-[26px] font-bold text-gray-900 tabular-nums leading-tight">
              {c.value.toLocaleString()}
            </div>
            <div className="text-[11px] text-gray-500 font-medium mt-1">{c.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-gray-200 mb-0">
        {(['overview', 'logs', 'nodes', 'edges'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="px-5 py-2.5 text-[12px] font-semibold uppercase tracking-[0.04em] border-b-2 -mb-px transition-colors duration-150"
            style={{
              borderBottomColor: tab === t ? '#b91c1c' : 'transparent',
              color: tab === t ? '#991b1b' : '#9ca3af',
            }}
          >
            {t === 'overview' ? 'Jurisdiction Overview' : t === 'logs' ? 'Live Logs' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="border border-t-0 border-gray-200 rounded-b-lg overflow-hidden bg-white">
        {/* ── OVERVIEW TAB ── */}
        {tab === 'overview' && (
          <div className="overflow-x-auto">
            {/* Table header */}
            <div
              className="grid text-[10px] font-bold uppercase tracking-[0.06em] text-white sticky top-0 z-10"
              style={{
                gridTemplateColumns: '120px 100px repeat(4, 1fr) 80px',
                background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
              }}
            >
              <div className="px-4 py-2.5">Jurisdiction</div>
              <div className="px-4 py-2.5">Status</div>
              <div className="px-4 py-2.5 text-right">Java</div>
              <div className="px-4 py-2.5 text-right">XSLT</div>
              <div className="px-4 py-2.5 text-right">Nodes</div>
              <div className="px-4 py-2.5 text-right">Edges</div>
              <div className="px-4 py-2.5">Action</div>
            </div>
            {/* Rows */}
            {(stats?.jurisdictions || []).map((j, i) => (
              <div
                key={j.id}
                className="grid text-[12px] border-b border-gray-50 hover:bg-red-50/30 transition-colors"
                style={{
                  gridTemplateColumns: '120px 100px repeat(4, 1fr) 80px',
                  background: i % 2 === 1 ? '#fafafa' : '#fff',
                }}
              >
                <div className="px-4 py-3 font-bold text-gray-900">{j.id.toUpperCase()}</div>
                <div className="px-4 py-3"><StatusBadge status={j.status} /></div>
                <div className="px-4 py-3 text-right tabular-nums text-gray-700">{j.java_findings}</div>
                <div className="px-4 py-3 text-right tabular-nums text-gray-700">{j.xslt_findings}</div>
                <div className="px-4 py-3 text-right tabular-nums text-gray-700">{j.nodes}</div>
                <div className="px-4 py-3 text-right tabular-nums text-gray-700">{j.edges}</div>
                <div className="px-4 py-3">
                  <button
                    onClick={() => { setSelectedJ(j.id); setTab('nodes'); }}
                    className="text-[10px] font-semibold text-brand hover:underline"
                  >
                    Explore
                  </button>
                </div>
              </div>
            ))}
            {(!stats?.jurisdictions || stats.jurisdictions.length === 0) && (
              <div className="px-4 py-12 text-center text-gray-400 text-[12px]">
                No jurisdiction data. Trigger a batch parse to populate.
              </div>
            )}
          </div>
        )}

        {/* ── LOGS TAB ── */}
        {tab === 'logs' && (
          <div className="max-h-[380px] overflow-y-auto font-mono text-[11px]">
            {(logs || []).map((log, i) => (
              <div key={i} className="flex gap-2 px-4 py-[5px] border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <span className="text-gray-400 w-[72px] shrink-0 tabular-nums">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span
                  className="w-[40px] shrink-0 font-bold uppercase"
                  style={{ color: LOG_COLORS[log.level] || '#999' }}
                >
                  {log.level}
                </span>
                {log.jurisdiction_id && (
                  <span className="px-1.5 py-px bg-gray-100 rounded text-gray-500 text-[10px] shrink-0">
                    {log.jurisdiction_id}
                  </span>
                )}
                <span className="text-gray-700">{log.message}</span>
              </div>
            ))}
            {(!logs || logs.length === 0) && (
              <div className="px-4 py-12 text-center text-gray-400 text-[12px] font-sans">
                No logs yet. Trigger a batch parse to see live output.
              </div>
            )}
          </div>
        )}

        {/* ── NODES TAB ── */}
        {tab === 'nodes' && (
          <div className="max-h-[380px] overflow-y-auto">
            {!selectedJ ? (
              <div className="px-4 py-12 text-center text-gray-400 text-[12px]">
                Select a jurisdiction from the Overview tab to view nodes
              </div>
            ) : (
              <>
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 text-[11px] text-gray-500">
                  Viewing nodes for <strong className="text-gray-800">{selectedJ.toUpperCase()}</strong>
                  <button onClick={() => setSelectedJ(null)} className="ml-2 text-brand hover:underline">clear</button>
                </div>
                <div
                  className="grid text-[10px] font-bold uppercase tracking-[0.06em] text-white sticky top-0 z-10"
                  style={{
                    gridTemplateColumns: '1fr 120px 1fr 60px',
                    background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
                  }}
                >
                  <div className="px-4 py-2">Node ID</div>
                  <div className="px-4 py-2">Type</div>
                  <div className="px-4 py-2">Label</div>
                  <div className="px-4 py-2">Line</div>
                </div>
                {(nodesData?.nodes || []).map((n, i) => (
                  <div
                    key={String(n.id)}
                    className="grid text-[11px] border-b border-gray-50 hover:bg-red-50/30"
                    style={{
                      gridTemplateColumns: '1fr 120px 1fr 60px',
                      background: i % 2 === 1 ? '#fafafa' : '#fff',
                    }}
                  >
                    <div className="px-4 py-[6px] font-mono text-[10px] text-gray-500 truncate">{String(n.id)}</div>
                    <div className="px-4 py-[6px]">
                      <span
                        className="px-1.5 py-px rounded text-[9px] font-bold"
                        style={{
                          background: String(n.type).includes('JAVA') ? '#fff7ed' : '#eff6ff',
                          color: String(n.type).includes('JAVA') ? '#c2410c' : '#1d4ed8',
                        }}
                      >
                        {String(n.type)}
                      </span>
                    </div>
                    <div className="px-4 py-[6px] font-medium text-gray-800 truncate">{String(n.label)}</div>
                    <div className="px-4 py-[6px] text-gray-400 tabular-nums">{n.line_number ? String(n.line_number) : '-'}</div>
                  </div>
                ))}
                <div className="px-4 py-2 text-[10px] text-gray-400 bg-gray-50">
                  Showing {nodesData?.nodes.length || 0} of {nodesData?.total || 0} nodes
                </div>
              </>
            )}
          </div>
        )}

        {/* ── EDGES TAB ── */}
        {tab === 'edges' && (
          <div className="max-h-[380px] overflow-y-auto">
            {!selectedJ ? (
              <div className="px-4 py-12 text-center text-gray-400 text-[12px]">
                Select a jurisdiction from the Overview tab to view edges
              </div>
            ) : (
              <>
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 text-[11px] text-gray-500">
                  Viewing edges for <strong className="text-gray-800">{selectedJ.toUpperCase()}</strong>
                  <button onClick={() => setSelectedJ(null)} className="ml-2 text-brand hover:underline">clear</button>
                </div>
                <div
                  className="grid text-[10px] font-bold uppercase tracking-[0.06em] text-white sticky top-0 z-10"
                  style={{
                    gridTemplateColumns: '1fr 130px 1fr',
                    background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
                  }}
                >
                  <div className="px-4 py-2">Source</div>
                  <div className="px-4 py-2">Type</div>
                  <div className="px-4 py-2">Target</div>
                </div>
                {(edgesData?.edges || []).map((e, i) => (
                  <div
                    key={`${e.source}-${e.target}-${i}`}
                    className="grid text-[11px] border-b border-gray-50 hover:bg-red-50/30"
                    style={{
                      gridTemplateColumns: '1fr 130px 1fr',
                      background: i % 2 === 1 ? '#fafafa' : '#fff',
                    }}
                  >
                    <div className="px-4 py-[6px] font-mono text-[10px] text-gray-500 truncate">{String(e.source)}</div>
                    <div className="px-4 py-[6px]">
                      <span className="px-1.5 py-px rounded text-[9px] font-bold bg-purple-50 text-purple-700">{String(e.type)}</span>
                    </div>
                    <div className="px-4 py-[6px] font-mono text-[10px] text-gray-500 truncate">{String(e.target)}</div>
                  </div>
                ))}
                <div className="px-4 py-2 text-[10px] text-gray-400 bg-gray-50">
                  Showing {edgesData?.edges.length || 0} of {edgesData?.total || 0} edges
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
