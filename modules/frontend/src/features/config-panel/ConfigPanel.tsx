import React, { useEffect, useState } from 'react';
import { X, Save } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { traceApi } from '../../api/traceApi';
import { Spinner } from '../../components/ui/Spinner';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-slate-900 border border-slate-700 rounded-xl w-[480px] max-h-[80vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
          <span className="text-sm font-semibold text-slate-200">Trace Configuration</span>
          <button onClick={() => setConfigOpen(false)} className="text-slate-500 hover:text-slate-300">
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <div className="flex flex-col gap-4">
              <ConfigField
                label="Max Depth"
                type="number"
                value={String(local.maxDepth ?? 20)}
                onChange={(v) => setLocal({ ...local, maxDepth: parseInt(v) || 20 })}
              />
              <ConfigToggle
                label="Follow Internal Calls Only"
                checked={Boolean(local.followInternalCallsOnly)}
                onChange={(v) => setLocal({ ...local, followInternalCallsOnly: v })}
              />
              <ConfigToggle
                label="Enable Condition Tracing"
                checked={Boolean(local.enableConditionTracing)}
                onChange={(v) => setLocal({ ...local, enableConditionTracing: v })}
              />
              <ConfigToggle
                label="Enable XSLT Imports"
                checked={Boolean(local.enableXsltImports)}
                onChange={(v) => setLocal({ ...local, enableXsltImports: v })}
              />
              <div>
                <label className="text-xs text-slate-500 mb-1.5 block">Include Packages (one per line)</label>
                <textarea
                  rows={3}
                  value={(local.includePackages as string[] || []).join('\n')}
                  onChange={(e) => setLocal({ ...local, includePackages: e.target.value.split('\n').filter(Boolean) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-xs font-mono text-slate-200
                             focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 mb-1.5 block">Exclude Packages (one per line)</label>
                <textarea
                  rows={3}
                  value={(local.excludePackages as string[] || []).join('\n')}
                  onChange={(e) => setLocal({ ...local, excludePackages: e.target.value.split('\n').filter(Boolean) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-xs font-mono text-slate-200
                             focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t border-slate-700 flex justify-end gap-3">
          <button onClick={() => setConfigOpen(false)} className="text-sm text-slate-400 hover:text-slate-200 px-3 py-1.5">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded
                       disabled:bg-slate-700 disabled:text-slate-500 transition-colors"
          >
            {saving ? <Spinner size="sm" /> : <Save size={14} />} Save
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfigField({ label, type, value, onChange }: { label: string; type: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="text-xs text-slate-500 mb-1.5 block">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-slate-200
                   focus:outline-none focus:border-blue-500"
      />
    </div>
  );
}

function ConfigToggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-400">{label}</span>
      <button
        onClick={() => onChange(!checked)}
        className={`w-10 h-5 rounded-full transition-colors relative ${checked ? 'bg-blue-600' : 'bg-slate-600'}`}
      >
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${checked ? 'translate-x-5' : ''}`} />
      </button>
    </div>
  );
}
