import React, { useEffect, useState } from 'react';
import { X, Save, Settings } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { traceApi } from '../../api/traceApi';

export function ConfigPanel() {
  const { configOpen, setConfigOpen, config, setConfig } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [local, setLocal] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (configOpen && !config) {
      setLoading(true);
      traceApi.getConfig()
        .then((c) => { setConfig(c); setLocal(c.trace as Record<string, unknown>); })
        .catch(() => {})
        .finally(() => setLoading(false));
    } else if (configOpen && config) {
      setLocal(config.trace as Record<string, unknown>);
    }
  }, [configOpen]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await traceApi.updateConfig(local as any);
      setConfig(updated);
    } catch { /* ignore */ }
    finally { setSaving(false); setConfigOpen(false); }
  };

  if (!configOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) setConfigOpen(false); }}
    >
      <div
        className="flex flex-col animate-fade-up"
        style={{
          width: 500,
          maxHeight: '80vh',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderTop: '2px solid var(--amber)',
          borderRadius: 6,
          boxShadow: '0 20px 60px rgba(0,0,0,0.7)',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-3.5 shrink-0"
          style={{ borderBottom: '1px solid var(--border)' }}
        >
          <div className="flex items-center gap-2.5">
            <div
              style={{
                width: 26, height: 26,
                background: 'var(--amber-glow)',
                border: '1px solid rgba(245,166,35,0.3)',
                borderRadius: 4,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <Settings size={12} style={{ color: 'var(--amber)' }} />
            </div>
            <span className="label-heading" style={{ color: 'var(--text-primary)', fontSize: '11px' }}>
              TRACE CONFIGURATION
            </span>
          </div>
          <button
            onClick={() => setConfigOpen(false)}
            className="flex items-center justify-center"
            style={{ width: 26, height: 26, borderRadius: 4, border: '1px solid var(--border)', color: 'var(--text-muted)' }}
          >
            <X size={12} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex justify-center items-center py-12 gap-3"
              style={{ color: 'var(--text-muted)' }}>
              <div
                style={{
                  width: 20, height: 20,
                  border: '1.5px solid var(--border-bright)',
                  borderTopColor: 'var(--amber)',
                  borderRadius: '50%',
                }}
                className="animate-spin"
              />
              <span style={{ fontSize: '11px' }}>Loading config…</span>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <ConfigField
                label="MAX DEPTH"
                type="number"
                value={String(local.maxDepth ?? 20)}
                hint="Maximum call chain depth to follow (1–50)"
                onChange={(v) => setLocal({ ...local, maxDepth: parseInt(v) || 20 })}
              />
              <ConfigToggle
                label="FOLLOW INTERNAL CALLS ONLY"
                checked={Boolean(local.followInternalCallsOnly)}
                onChange={(v) => setLocal({ ...local, followInternalCallsOnly: v })}
              />
              <ConfigToggle
                label="ENABLE CONDITION TRACING"
                checked={Boolean(local.enableConditionTracing)}
                onChange={(v) => setLocal({ ...local, enableConditionTracing: v })}
              />
              <ConfigToggle
                label="ENABLE XSLT IMPORTS"
                checked={Boolean(local.enableXsltImports)}
                onChange={(v) => setLocal({ ...local, enableXsltImports: v })}
              />
              <ConfigTextArea
                label="INCLUDE PACKAGES"
                hint="Java packages to deep-scan (one per line)"
                value={(local.includePackages as string[] || []).join('\n')}
                onChange={(v) => setLocal({ ...local, includePackages: v.split('\n').filter(Boolean) })}
              />
              <ConfigTextArea
                label="EXCLUDE PACKAGES"
                hint="Packages to skip (one per line)"
                value={(local.excludePackages as string[] || []).join('\n')}
                onChange={(v) => setLocal({ ...local, excludePackages: v.split('\n').filter(Boolean) })}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-2.5 px-5 py-3.5 shrink-0"
          style={{ borderTop: '1px solid var(--border)' }}
        >
          <button
            onClick={() => setConfigOpen(false)}
            className="st-btn-ghost"
          >
            CANCEL
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="st-btn-primary"
            style={{ opacity: saving ? 0.5 : 1 }}
          >
            {saving ? (
              <>
                <div
                  style={{
                    width: 10, height: 10,
                    border: '1.5px solid transparent',
                    borderTopColor: 'currentColor',
                    borderRadius: '50%',
                  }}
                  className="animate-spin"
                />
                SAVING…
              </>
            ) : (
              <><Save size={11} /> SAVE CONFIG</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfigField({
  label, type, value, hint, onChange,
}: {
  label: string; type: string; value: string; hint?: string; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="label-heading block mb-1.5" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>
        {label}
      </label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="st-input" />
      {hint && (
        <p style={{ marginTop: 4, fontSize: '10px', color: 'var(--text-muted)', fontFamily: "'IBM Plex Mono', monospace" }}>
          {hint}
        </p>
      )}
    </div>
  );
}

function ConfigTextArea({
  label, hint, value, onChange,
}: {
  label: string; hint?: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="label-heading block mb-1.5" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>
        {label}
      </label>
      <textarea
        rows={3}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="st-input"
        style={{ resize: 'none', fontFamily: "'IBM Plex Mono', monospace", fontSize: '11px' }}
      />
      {hint && (
        <p style={{ marginTop: 4, fontSize: '10px', color: 'var(--text-muted)', fontFamily: "'IBM Plex Mono', monospace" }}>
          {hint}
        </p>
      )}
    </div>
  );
}

function ConfigToggle({
  label, checked, onChange,
}: {
  label: string; checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div
      className="flex items-center justify-between py-2"
      style={{ borderBottom: '1px solid var(--border)' }}
    >
      <span className="label-tag" style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>{label}</span>
      <button
        onClick={() => onChange(!checked)}
        style={{
          width: 36, height: 20,
          borderRadius: 10,
          background: checked ? 'var(--amber)' : 'var(--bg-elevated)',
          border: checked ? 'none' : '1px solid var(--border-bright)',
          position: 'relative',
          transition: 'background 0.2s',
          cursor: 'pointer',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            position: 'absolute',
            top: 2, left: checked ? 18 : 2,
            width: 14, height: 14,
            borderRadius: '50%',
            background: checked ? '#06080f' : 'var(--text-muted)',
            transition: 'left 0.15s',
          }}
        />
      </button>
    </div>
  );
}
