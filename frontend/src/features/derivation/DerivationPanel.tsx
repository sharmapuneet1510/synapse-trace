import React, { useCallback, useEffect, useState } from 'react';
import { Sparkles, X, RefreshCw, Copy, Check, ChevronDown } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { deriveField, listPrompts } from '../../api/lineageApi';

const PROMPT_META: Record<string, { desc: string; color: string }> = {
  business_derivation: { desc: 'Plain-English explanation of how the field is derived', color: 'var(--amber)' },
  technical_summary:   { desc: 'Developer-oriented call-chain and logic summary',        color: 'var(--cyan)' },
  reporting_logic:     { desc: 'How the field drives report inclusion / categorisation', color: 'var(--violet)' },
  enrichment_logic:    { desc: 'Extraction → enrichment → override chain',              color: 'var(--emerald)' },
  downstream_impact:   { desc: 'Fields, reports and systems that depend on this field',  color: '#f59e0b' },
  examples:            { desc: '5 worked trade scenarios exercising every branch',       color: 'var(--coral)' },
  operations:          { desc: 'Production runbook: happy path, fallbacks, monitoring',  color: '#06b6d4' },
  field_impact:        { desc: 'Change impact analysis for safe modifications',          color: 'var(--red)' },
  chat_context:        { desc: 'Compact context block for chat queries',                 color: 'var(--text-secondary)' },
};

export function DerivationPanel() {
  const {
    derivationOpen, setDerivationOpen,
    derivationText, setDerivationText,
    derivationPrompt, setDerivationPrompt,
    isDerivationLoading, setDerivationLoading,
    traceResult,
  } = useAppStore();

  const [prompts, setPrompts] = useState<string[]>(Object.keys(PROMPT_META));
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!derivationOpen) return;
    listPrompts()
      .then((r) => { if (r.prompts.length) setPrompts(r.prompts); })
      .catch(console.error);
  }, [derivationOpen]);

  const handleRun = useCallback(async () => {
    if (!traceResult || isDerivationLoading) return;
    setDerivationLoading(true);
    setDerivationText(null);
    setError(null);
    try {
      const resp = await deriveField({
        field_name: traceResult.field_name,
        project_repos: [],
        prompt_name: derivationPrompt,
      });
      setDerivationText(resp.derivation);
    } catch (e: any) {
      setError(e.message ?? 'Derivation failed');
    } finally {
      setDerivationLoading(false);
    }
  }, [traceResult, derivationPrompt, isDerivationLoading]);

  const handleCopy = useCallback(() => {
    if (!derivationText) return;
    navigator.clipboard.writeText(derivationText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [derivationText]);

  if (!derivationOpen) return null;

  const meta = PROMPT_META[derivationPrompt] || { desc: '', color: 'var(--amber)' };

  return (
    <div className="st-panel animate-panel" style={{ width: 520 }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 shrink-0"
        style={{ height: 48, borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2.5">
          <div
            style={{
              width: 28, height: 28,
              background: 'var(--amber-glow)',
              border: '1px solid rgba(245,166,35,0.3)',
              borderRadius: 4,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Sparkles size={13} style={{ color: 'var(--amber)' }} />
          </div>
          <div>
            <span className="label-heading" style={{ color: 'var(--text-primary)', fontSize: '11px' }}>
              AI DERIVATION
            </span>
            {traceResult && (
              <span
                style={{
                  display: 'block',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: '10px',
                  color: 'var(--amber)',
                  marginTop: 1,
                }}
              >
                {traceResult.field_name}
              </span>
            )}
          </div>
        </div>
        <PanelCloseBtn onClick={() => setDerivationOpen(false)} />
      </div>

      {/* Amber accent */}
      <div style={{ height: 1.5, background: 'var(--amber)', opacity: 0.5 }} />

      {/* Controls */}
      <div
        className="px-4 py-3 flex flex-col gap-3 shrink-0"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div>
          <label
            className="label-heading block mb-1.5"
            style={{ color: 'var(--text-muted)', fontSize: '9px' }}
          >
            PROMPT TEMPLATE
          </label>
          <div className="relative">
            <select
              value={derivationPrompt}
              onChange={(e) => setDerivationPrompt(e.target.value)}
              className="st-select w-full"
            >
              {prompts.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <ChevronDown
              size={11}
              style={{
                position: 'absolute', right: 9, top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
                pointerEvents: 'none',
              }}
            />
          </div>
          {meta.desc && (
            <p
              style={{
                marginTop: 5,
                fontSize: '10px',
                color: meta.color,
                fontFamily: "'IBM Plex Mono', monospace",
                lineHeight: 1.4,
              }}
            >
              {meta.desc}
            </p>
          )}
        </div>

        <button
          onClick={handleRun}
          disabled={!traceResult || isDerivationLoading}
          className="st-btn-primary"
          style={{
            width: '100%',
            justifyContent: 'center',
            opacity: !traceResult || isDerivationLoading ? 0.4 : 1,
            cursor: !traceResult || isDerivationLoading ? 'not-allowed' : 'pointer',
          }}
        >
          {isDerivationLoading ? (
            <><RefreshCw size={12} className="animate-spin" /> GENERATING…</>
          ) : (
            <><Sparkles size={12} /> RUN DERIVATION</>
          )}
        </button>

        {!traceResult && (
          <p style={{ fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center' }}>
            Run a trace first to enable derivation.
          </p>
        )}
      </div>

      {/* Output */}
      <div className="flex-1 overflow-y-auto">
        {error && (
          <div
            className="m-4 p-3 rounded"
            style={{
              background: 'rgba(248,113,113,0.06)',
              border: '1px solid rgba(248,113,113,0.3)',
              color: 'var(--red)',
              fontSize: '11px',
              fontFamily: "'IBM Plex Mono', monospace",
            }}
          >
            {error}
          </div>
        )}

        {derivationText && (
          <div className="relative m-3">
            {/* Copy button */}
            <button
              onClick={handleCopy}
              className="absolute top-3 right-3 flex items-center gap-1.5 transition-all"
              style={{
                padding: '4px 8px',
                borderRadius: 3,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-bright)',
                color: copied ? 'var(--emerald)' : 'var(--text-muted)',
                fontSize: '9px',
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 600,
                letterSpacing: '0.08em',
                cursor: 'pointer',
              }}
            >
              {copied ? <Check size={10} /> : <Copy size={10} />}
              {copied ? 'COPIED' : 'COPY'}
            </button>

            <div
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderTop: '2px solid var(--amber)',
                borderRadius: 5,
                padding: '14px 14px 14px 14px',
                paddingTop: 40,
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: '11px',
                color: 'var(--text-secondary)',
                lineHeight: 1.7,
                whiteSpace: 'pre-wrap',
              }}
            >
              {derivationText}
            </div>
          </div>
        )}

        {!derivationText && !isDerivationLoading && !error && (
          <div className="flex flex-col items-center justify-center h-full gap-4 p-8"
            style={{ color: 'var(--text-muted)' }}>
            <Sparkles size={32} style={{ opacity: 0.2 }} />
            <p style={{ fontSize: '11px', textAlign: 'center', lineHeight: 1.6, maxWidth: 300 }}>
              Select a prompt template and click{' '}
              <span style={{ color: 'var(--amber)' }}>RUN DERIVATION</span>{' '}
              to generate an AI-powered analysis of the field's business logic.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function PanelCloseBtn({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center justify-center transition-all"
      style={{
        width: 26, height: 26, borderRadius: 4,
        color: 'var(--text-muted)',
        border: '1px solid var(--border)',
        background: 'transparent',
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
      <X size={12} />
    </button>
  );
}
