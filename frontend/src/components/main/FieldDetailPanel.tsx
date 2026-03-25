import { useState } from 'react';
import { useAppStore } from '../../stores/appStore';
import { useFieldDetail } from '../../hooks/useFieldDetail';
import { useTranslation } from '../../hooks/useTranslation';
import XsltLogicBlock from './XsltLogicBlock';
import DependencyList from './DependencyList';
import InputXPathsTable from './InputXPathsTable';
import AssetClassSelector from './AssetClassSelector';

const TRANSLATION_TABS = [
  { key: 'business_derivation', label: 'Derivation' },
  { key: 'reporting_logic', label: 'Reporting Logic' },
  { key: 'internal_enrichment', label: 'Enrichment' },
  { key: 'downstream_mapping', label: 'Downstream' },
  { key: 'examples', label: 'Examples' },
  { key: 'operational_guidance', label: 'Operations' },
] as const;

type TabKey = (typeof TRANSLATION_TABS)[number]['key'];

export default function FieldDetailPanel() {
  const {
    jurisdictionId,
    fieldName,
    configType,
    assetClass,
    setAssetClass,
    detailViewMode,
    setDetailViewMode,
  } = useAppStore();
  const { data: detail, isLoading } = useFieldDetail(jurisdictionId, fieldName);
  const { data: translation, isLoading: translationLoading } = useTranslation(
    fieldName, jurisdictionId, !!fieldName && !!jurisdictionId,
  );
  const [activeTransTab, setActiveTransTab] = useState<TabKey>('business_derivation');

  /* Empty state */
  if (!jurisdictionId || !fieldName) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
          style={{ background: 'linear-gradient(135deg, #fef2f2, #fee2e2)' }}
        >
          <svg className="w-8 h-8 text-brand" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
          </svg>
        </div>
        <div className="text-[15px] font-semibold text-gray-700 mb-1">Select a Field</div>
        <div className="text-[13px] text-gray-400 max-w-[300px]">
          Choose a jurisdiction, report type, and field from the sidebar to explore its business logic and data lineage.
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full gap-3">
        <div className="w-6 h-6 border-[2.5px] border-gray-200 border-t-brand rounded-full animate-spin" />
        <span className="text-[13px] text-gray-400">Loading field details...</span>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-[13px]">
        Field not found.
      </div>
    );
  }

  const renderTranslationContent = () => {
    if (translationLoading) {
      return (
        <div className="flex items-center gap-2 py-8 justify-center">
          <div className="w-4 h-4 border-2 border-gray-200 border-t-brand rounded-full animate-spin" />
          <span className="text-[12px] text-gray-400">Loading business translation...</span>
        </div>
      );
    }
    if (!translation) {
      return <div className="text-gray-400 text-[12px] py-6 text-center">No translation data available</div>;
    }
    if (activeTransTab === 'examples') {
      return (
        <div className="space-y-3 py-1">
          {translation.examples.map((ex, i) => (
            <div key={i} className="p-3.5 bg-gray-50 rounded-lg border border-gray-100">
              <div className="text-[10px] font-bold text-brand uppercase tracking-[0.06em] mb-1">
                Example {i + 1}
              </div>
              <div className="text-[12.5px] text-gray-700 leading-relaxed">{ex}</div>
            </div>
          ))}
        </div>
      );
    }
    return (
      <div className="text-[12.5px] text-gray-700 leading-[1.8] whitespace-pre-wrap py-1">
        {translation[activeTransTab]}
      </div>
    );
  };

  return (
    <div className="p-5 pb-12 max-w-[1000px]">
      {/* ─── Header row ─── */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="min-w-0">
          <h2 className="text-[20px] font-bold text-gray-900 tracking-[-0.02em] leading-tight mb-1">
            {detail.header}
          </h2>
          <div className="flex items-center gap-2 text-[11px]">
            <code className="px-2 py-0.5 bg-gray-100 rounded text-[10.5px] text-gray-500 font-mono border border-gray-200">
              {detail.field_name}
            </code>
            {configType && (
              <span
                className="px-2.5 py-0.5 text-[10px] font-bold rounded-full text-white tracking-wide"
                style={{ background: 'linear-gradient(135deg, #dc2626, #b91c1c)' }}
              >
                {configType}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <AssetClassSelector
            classes={detail.asset_classes}
            selected={assetClass}
            onSelect={setAssetClass}
          />
          <div className="view-toggle">
            <button
              className={detailViewMode === 'business' ? 'active' : ''}
              onClick={() => setDetailViewMode('business')}
            >
              Business
            </button>
            <button
              className={detailViewMode === 'technical' ? 'active' : ''}
              onClick={() => setDetailViewMode('technical')}
            >
              Technical
            </button>
          </div>
        </div>
      </div>

      {/* ── BUSINESS VIEW ── */}
      {detailViewMode === 'business' && (
        <div className="space-y-4">
          {/* Inline Business Translation — the main content */}
          <div className="glass-card">
            <div className="section-bar" style={{ borderRadius: '12px 12px 0 0' }}>
              <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>Business Translation</span>
            </div>
            <div className="translation-tabs px-2">
              {TRANSLATION_TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTransTab(tab.key)}
                  className={activeTransTab === tab.key ? 'active' : ''}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="px-5 py-4 min-h-[120px]">
              {renderTranslationContent()}
            </div>
          </div>

          {/* Quick stats row */}
          <div className="grid grid-cols-3 gap-3">
            <div className="glass-card p-4">
              <div className="text-[10px] font-bold uppercase tracking-[0.06em] text-gray-400 mb-1">Dependencies</div>
              <div className="text-[22px] font-bold text-gray-900 tabular-nums">{detail.dependencies.length}</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-[10px] font-bold uppercase tracking-[0.06em] text-gray-400 mb-1">Data Sources</div>
              <div className="text-[22px] font-bold text-gray-900 tabular-nums">{detail.input_xpaths.length}</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-[10px] font-bold uppercase tracking-[0.06em] text-gray-400 mb-1">Jurisdiction</div>
              <div className="text-[22px] font-bold text-brand tabular-nums">{jurisdictionId?.toUpperCase()}</div>
            </div>
          </div>

          {/* Dependencies in business view */}
          {detail.dependencies.length > 0 && (
            <DependencyList dependencies={detail.dependencies} />
          )}
        </div>
      )}

      {/* ── TECHNICAL VIEW ── */}
      {detailViewMode === 'technical' && (
        <div className="space-y-4">
          {/* XSLT Logic */}
          <XsltLogicBlock logic={detail.xslt_logic} file={detail.xslt_file} line={detail.xslt_line} />

          {/* Dependencies */}
          <DependencyList dependencies={detail.dependencies} />

          {/* XPaths Table */}
          <InputXPathsTable xpaths={detail.input_xpaths} />
        </div>
      )}
    </div>
  );
}
