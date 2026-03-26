/**
 * TracePanel — Variable lineage trace UI.
 * Allows tracing any variable name (and custom aliases) through the parsed
 * lineage graph, with an interactive SVG graph output.
 */
import { useState } from 'react';
import { useTraceVariable } from '../../hooks/useTrace';
import LineageGraph from './LineageGraph';
import type { TraceResponse } from '../../types/trace';

interface Props {
  defaultVariable?: string;
  defaultJurisdiction?: string;
}

const NODE_TYPE_COLORS: Record<string, string> = {
  JAVA_CLASS:    '#c2410c',
  JAVA_METHOD:   '#d97706',
  JAVA_FIELD:    '#dc2626',
  JAVA_CONSTANT: '#9333ea',
  DTO:           '#16a34a',
  XSLT_FILE:     '#2563eb',
  XSLT_TEMPLATE: '#0891b2',
  XSLT_FIELD:    '#6366f1',
};

export default function TracePanel({ defaultVariable = '', defaultJurisdiction = '' }: Props) {
  const [variableName, setVariableName] = useState(defaultVariable);
  const [jurisdictionId, setJurisdictionId] = useState(defaultJurisdiction);
  const [extraVariations, setExtraVariations] = useState('');
  const [result, setResult] = useState<TraceResponse | null>(null);
  const traceMutation = useTraceVariable();

  const handleTrace = () => {
    if (!variableName.trim() || !jurisdictionId.trim()) return;
    const extras = extraVariations.split(',').map((s) => s.trim()).filter(Boolean);
    traceMutation.mutate(
      {
        variable_name: variableName.trim(),
        jurisdiction_id: jurisdictionId.trim().toLowerCase(),
        additional_variations: extras,
        max_depth: 15,
      },
      { onSuccess: (data) => setResult(data) },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleTrace();
  };

  // Group nodes by type for the legend
  const nodeTypeCounts = result?.nodes.reduce<Record<string, number>>((acc, n) => {
    acc[n.node_type] = (acc[n.node_type] || 0) + 1;
    return acc;
  }, {}) || {};

  return (
    <div className="glass-card">
      <div className="section-bar" style={{ borderRadius: '12px 12px 0 0' }}>
        <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          <path d="M11 8v3l2 2" />
        </svg>
        <span>Variable Trace</span>
        {result && (
          <span className="section-count">
            ({result.node_count} nodes · {result.edge_count} edges)
          </span>
        )}
      </div>

      {/* Input row */}
      <div className="p-4 border-b border-gray-100 bg-gray-50/50">
        <div className="flex gap-2 flex-wrap items-end">
          <div className="flex-1 min-w-[140px]">
            <label className="text-[10px] font-bold uppercase tracking-[0.06em] text-gray-400 block mb-1">
              Variable Name
            </label>
            <input
              type="text"
              value={variableName}
              onChange={(e) => setVariableName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. N_EFFECTIVE_DATE"
              className="w-full px-3 py-2 text-[12px] border border-gray-200 rounded-lg bg-white font-mono focus:outline-none focus:ring-2 focus:ring-brand/15 focus:border-brand/30"
            />
          </div>
          <div className="w-[110px]">
            <label className="text-[10px] font-bold uppercase tracking-[0.06em] text-gray-400 block mb-1">
              Jurisdiction
            </label>
            <input
              type="text"
              value={jurisdictionId}
              onChange={(e) => setJurisdictionId(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. hkma"
              className="w-full px-3 py-2 text-[12px] border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand/15 focus:border-brand/30"
            />
          </div>
          <div className="flex-1 min-w-[160px]">
            <label className="text-[10px] font-bold uppercase tracking-[0.06em] text-gray-400 block mb-1">
              Extra Aliases <span className="normal-case font-normal opacity-60">(comma-separated, optional)</span>
            </label>
            <input
              type="text"
              value={extraVariations}
              onChange={(e) => setExtraVariations(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. effectiveDate, EFFECTIVE_DT"
              className="w-full px-3 py-2 text-[12px] border border-gray-200 rounded-lg bg-white font-mono focus:outline-none focus:ring-2 focus:ring-brand/15 focus:border-brand/30"
            />
          </div>
          <button
            onClick={handleTrace}
            disabled={!variableName.trim() || !jurisdictionId.trim() || traceMutation.isPending}
            className="px-5 py-2 text-[12px] font-semibold text-white rounded-lg transition-all disabled:opacity-40 hover:shadow-lg active:scale-95"
            style={{ background: 'linear-gradient(135deg, #dc2626, #b91c1c)' }}
          >
            {traceMutation.isPending ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Tracing...
              </span>
            ) : 'Trace →'}
          </button>
        </div>

        {/* Auto-generated variations notice */}
        {result && result.variations_searched.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5 items-center">
            <span className="text-[10px] text-gray-400 font-medium">Searched variations:</span>
            {result.variations_searched.slice(0, 12).map((v) => (
              <code key={v} className="text-[9px] px-1.5 py-px bg-gray-100 rounded border border-gray-200 text-gray-600">
                {v}
              </code>
            ))}
            {result.variations_searched.length > 12 && (
              <span className="text-[9px] text-gray-400">+{result.variations_searched.length - 12} more</span>
            )}
          </div>
        )}
      </div>

      {/* Error / status */}
      {traceMutation.isError && (
        <div className="px-4 py-3 text-[12px] text-red-600 bg-red-50 border-b border-red-100">
          Trace failed. Make sure a batch parse has been run for this jurisdiction.
        </div>
      )}

      {result && result.parse_status !== 'ready' && (
        <div className="px-4 py-3 text-[12px] text-amber-700 bg-amber-50 border-b border-amber-100 flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          Parse status: <strong>{result.parse_status}</strong> — trigger a batch parse first to see graph data.
        </div>
      )}

      {result && result.node_count === 0 && result.parse_status === 'ready' && (
        <div className="px-4 py-8 text-center text-gray-400 text-[12px]">
          No nodes found for <code className="font-mono">{result.variable_name}</code> in {result.jurisdiction_id.toUpperCase()}.
          Try a different name or check the spelling.
        </div>
      )}

      {/* Legend */}
      {result && result.node_count > 0 && (
        <div className="px-4 py-2.5 border-b border-gray-100 flex flex-wrap gap-x-4 gap-y-1 bg-white">
          {Object.entries(nodeTypeCounts).map(([type, count]) => (
            <span key={type} className="flex items-center gap-1.5 text-[10px] text-gray-600">
              <span
                className="w-2 h-2 rounded-sm"
                style={{ background: NODE_TYPE_COLORS[type] || '#9ca3af' }}
              />
              {type.replace('JAVA_', 'Java ').replace('XSLT_', 'XSLT ')} ({count})
            </span>
          ))}
        </div>
      )}

      {/* Graph */}
      {result && result.node_count > 0 && (
        <div className="bg-gray-50/30">
          <LineageGraph data={result} height={480} />
        </div>
      )}
    </div>
  );
}
