import { useState } from 'react';
import { useTranslation } from '../../hooks/useTranslation';

interface Props {
  fieldName: string;
  jurisdictionId: string;
  onClose: () => void;
}

const TABS = [
  { key: 'business_derivation', label: 'PDM Derivation' },
  { key: 'reporting_logic', label: 'Troy Reporting Logic' },
  { key: 'internal_enrichment', label: 'Troy Internal Enrichment' },
  { key: 'downstream_mapping', label: 'Downstream Mapping' },
  { key: 'examples', label: 'Examples' },
  { key: 'operational_guidance', label: 'Operational Guidance' },
] as const;

type TabKey = (typeof TABS)[number]['key'];

export default function BusinessTranslation({ fieldName, jurisdictionId, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<TabKey>('business_derivation');
  const { data, isLoading } = useTranslation(fieldName, jurisdictionId, true);

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-16">
          <div className="w-6 h-6 border-2 border-gray-200 border-t-brand rounded-full animate-spin" />
        </div>
      );
    }
    if (!data) {
      return (
        <div className="text-gray-400 text-[13px] py-12 text-center">
          No translation data available
        </div>
      );
    }

    if (activeTab === 'examples') {
      return (
        <div className="space-y-4">
          {data.examples.map((ex, i) => (
            <div key={i} className="p-4 bg-gray-50 rounded-lg border border-gray-100">
              <div className="text-[12px] font-bold text-brand uppercase tracking-wide mb-1.5">
                Example {i + 1}
              </div>
              <div className="text-[13px] text-gray-700 leading-relaxed">{ex}</div>
            </div>
          ))}
        </div>
      );
    }

    const content = data[activeTab];
    return (
      <div className="text-[13px] text-gray-700 leading-[1.75] whitespace-pre-wrap">{content}</div>
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-3.5"
          style={{ background: 'linear-gradient(135deg, #991b1b, #7f1d1d)' }}
        >
          <div className="flex items-center gap-2.5 text-white">
            <svg className="w-[18px] h-[18px] opacity-80" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            <span className="font-bold text-[14px] tracking-[-0.01em]">Business Translation</span>
          </div>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-white transition-colors p-1 rounded hover:bg-white/10"
          >
            <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50 px-3 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="shrink-0 px-4 py-2.5 text-[12px] font-medium transition-all duration-150 border-b-2 -mb-px"
              style={{
                borderBottomColor: activeTab === tab.key ? '#b91c1c' : 'transparent',
                color: activeTab === tab.key ? '#991b1b' : '#6b7280',
                fontWeight: activeTab === tab.key ? 700 : 500,
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">{renderContent()}</div>
      </div>
    </div>
  );
}
