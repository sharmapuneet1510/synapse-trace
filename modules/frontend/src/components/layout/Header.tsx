import React from 'react';
import {
  Layers, Network, Settings, ScrollText,
  MessageCircle, Sparkles, BookOpen, Activity, Zap,
} from 'lucide-react';
import { useAppStore } from '../../store/appStore';

const ORIGIN_LABELS: Record<string, string> = {
  XSLT_THEN_JAVA: 'XSLT→JAVA',
  XSLT: 'XSLT',
  JAVA: 'JAVA',
  UNKNOWN: 'UNKNOWN',
};

export function Header() {
  const {
    traceResult, viewMode, setViewMode,
    setConfigOpen, setLogsOpen, logsOpen,
    setChatOpen, chatOpen,
    setDerivationOpen, derivationOpen,
    setApiDocsOpen, apiDocsOpen,
  } = useAppStore();

  const closeOthers = (except: string) => {
    if (except !== 'chat') setChatOpen(false);
    if (except !== 'derive') setDerivationOpen(false);
    if (except !== 'docs') setApiDocsOpen(false);
  };

  return (
    <header
      style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border)' }}
      className="h-12 flex items-center px-4 gap-4 shrink-0"
    >
      {/* Logo mark */}
      <div className="flex items-center gap-2 shrink-0">
        <div className="relative w-6 h-6 flex items-center justify-center">
          <Activity size={16} style={{ color: 'var(--amber)' }} />
        </div>
        <span
          style={{
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 700,
            fontSize: '17px',
            letterSpacing: '0.15em',
            color: 'var(--text-primary)',
          }}
        >
          SYNAPSE<span style={{ color: 'var(--amber)' }}>TRACE</span>
        </span>
      </div>

      {/* Divider */}
      <div style={{ width: 1, height: 20, background: 'var(--border-bright)' }} className="shrink-0" />

      {/* Field info badge */}
      {traceResult ? (
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="label-tag" style={{ color: 'var(--text-muted)' }}>FIELD</span>
          <span style={{ color: 'var(--amber)', fontWeight: 500, fontSize: '13px' }} className="font-mono truncate">
            {traceResult.field_name}
          </span>

          <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-bright)', borderRadius: 3 }}
            className="flex items-center gap-1.5 px-2 py-0.5"
          >
            <span className="status-dot green" />
            <span className="label-tag" style={{ color: 'var(--emerald)' }}>
              {ORIGIN_LABELS[traceResult.origin] ?? traceResult.origin}
            </span>
          </div>

          <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
            {traceResult.summary.total_nodes} nodes
          </span>
          <span style={{ color: 'var(--border-bright)', fontSize: '11px' }}>·</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
            {traceResult.summary.branch_count} branches
          </span>
          {traceResult.summary.has_xslt && (
            <span className="label-tag px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(167,139,250,0.12)', color: 'var(--violet)', border: '1px solid rgba(167,139,250,0.25)' }}>
              XSLT
            </span>
          )}
          {traceResult.summary.has_java && (
            <span className="label-tag px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(34,211,238,0.08)', color: 'var(--cyan)', border: '1px solid rgba(34,211,238,0.2)' }}>
              JAVA
            </span>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center gap-2">
          <span style={{ color: 'var(--text-muted)', fontSize: '11px', fontStyle: 'italic' }}>
            No active trace — enter a field name to begin
          </span>
        </div>
      )}

      <div className="flex-1" />

      {/* View toggle */}
      {traceResult && (
        <div
          className="flex items-center p-0.5 gap-0.5"
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-bright)', borderRadius: 5 }}
        >
          <button
            onClick={() => setViewMode('pipeline')}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-all"
            style={viewMode === 'pipeline'
              ? { background: 'var(--amber)', color: '#06080f' }
              : { color: 'var(--text-secondary)' }}
          >
            <Layers size={11} />
            <span className="label-tag" style={{ fontSize: '10px' }}>PIPELINE</span>
          </button>
          <button
            onClick={() => setViewMode('branch')}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-all"
            style={viewMode === 'branch'
              ? { background: 'var(--amber)', color: '#06080f' }
              : { color: 'var(--text-secondary)' }}
          >
            <Network size={11} />
            <span className="label-tag" style={{ fontSize: '10px' }}>BRANCH</span>
          </button>
        </div>
      )}

      {/* Toolbar icons */}
      <div className="flex items-center" style={{ gap: 2 }}>
        <HeaderIconBtn
          active={derivationOpen}
          activeColor="var(--amber)"
          activeBg="rgba(245,166,35,0.1)"
          title="AI Derivation"
          onClick={() => { closeOthers('derive'); setDerivationOpen(!derivationOpen); }}
        >
          <Sparkles size={14} />
        </HeaderIconBtn>

        <HeaderIconBtn
          active={chatOpen}
          activeColor="var(--emerald)"
          activeBg="rgba(16,185,129,0.1)"
          title="AI Chat"
          onClick={() => { closeOthers('chat'); setChatOpen(!chatOpen); }}
        >
          <MessageCircle size={14} />
        </HeaderIconBtn>

        <HeaderIconBtn
          active={apiDocsOpen}
          activeColor="var(--violet)"
          activeBg="rgba(167,139,250,0.1)"
          title="API Documentation"
          onClick={() => { closeOthers('docs'); setApiDocsOpen(!apiDocsOpen); }}
        >
          <BookOpen size={14} />
        </HeaderIconBtn>

        <div style={{ width: 1, height: 16, background: 'var(--border-bright)', margin: '0 4px' }} />

        <HeaderIconBtn
          active={logsOpen}
          activeColor="var(--text-primary)"
          activeBg="var(--bg-elevated)"
          title="Toggle logs"
          onClick={() => setLogsOpen(!logsOpen)}
        >
          <ScrollText size={14} />
        </HeaderIconBtn>

        <HeaderIconBtn
          active={false}
          activeColor="var(--text-primary)"
          activeBg="var(--bg-elevated)"
          title="Configuration"
          onClick={() => setConfigOpen(true)}
        >
          <Settings size={14} />
        </HeaderIconBtn>
      </div>
    </header>
  );
}

function HeaderIconBtn({
  children, active, activeColor, activeBg, title, onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  activeColor: string;
  activeBg: string;
  title: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="flex items-center justify-center transition-all"
      style={{
        width: 30,
        height: 30,
        borderRadius: 4,
        border: active ? `1px solid ${activeColor}30` : '1px solid transparent',
        color: active ? activeColor : 'var(--text-secondary)',
        background: active ? activeBg : 'transparent',
      }}
      onMouseEnter={(e) => {
        if (!active) {
          (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-primary)';
          (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-elevated)';
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)';
          (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
        }
      }}
    >
      {children}
    </button>
  );
}
