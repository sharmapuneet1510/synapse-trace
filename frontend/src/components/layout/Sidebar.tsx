import { useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import { useJurisdictions, useConfigType } from '../../hooks/useJurisdictions';
import JurisdictionSelector from '../sidebar/JurisdictionSelector';
import ConfigTypeTabs from '../sidebar/ConfigTypeTabs';
import FieldList from '../sidebar/FieldList';

export default function Sidebar() {
  const { jurisdictionId, configType, setJurisdiction, setConfigType } = useAppStore();
  const { data: jurisdictions } = useJurisdictions();
  const { data: configData } = useConfigType(jurisdictionId, configType);

  useEffect(() => {
    if (jurisdictions?.length && !jurisdictionId) {
      setJurisdiction(jurisdictions[0].id);
    }
  }, [jurisdictions, jurisdictionId, setJurisdiction]);

  useEffect(() => {
    if (jurisdictions && jurisdictionId && !configType) {
      const j = jurisdictions.find((j) => j.id === jurisdictionId);
      if (j?.config_types.length) {
        setConfigType(j.config_types[0]);
      }
    }
  }, [jurisdictions, jurisdictionId, configType, setConfigType]);

  const currentJurisdiction = jurisdictions?.find((j) => j.id === jurisdictionId);

  return (
    <aside
      className="w-[280px] bg-white border-r border-gray-200/80 flex flex-col shrink-0 overflow-hidden"
      style={{ boxShadow: '1px 0 8px rgba(0,0,0,0.02)' }}
    >
      {/* Jurisdiction */}
      <div className="p-3.5 pb-3 border-b border-gray-100">
        <div className="flex items-center gap-1.5 mb-2.5">
          <div className="w-5 h-5 rounded flex items-center justify-center bg-red-50">
            <svg className="w-3 h-3 text-brand" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
            </svg>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-gray-400">
            Jurisdiction
          </span>
        </div>
        <JurisdictionSelector
          jurisdictions={jurisdictions || []}
          selected={jurisdictionId}
          onSelect={setJurisdiction}
        />
      </div>

      {/* Report Type */}
      {currentJurisdiction && (
        <div className="px-3.5 pt-3 pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-1.5 mb-2.5">
            <div className="w-5 h-5 rounded flex items-center justify-center bg-red-50">
              <svg className="w-3 h-3 text-brand" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-gray-400">
              Report Type
            </span>
          </div>
          <ConfigTypeTabs
            types={currentJurisdiction.config_types}
            selected={configType}
            onSelect={setConfigType}
          />
        </div>
      )}

      {/* Fields */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-3.5 pt-3 pb-2 flex items-center gap-1.5">
          <div className="w-5 h-5 rounded flex items-center justify-center bg-red-50">
            <svg className="w-3 h-3 text-brand" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" />
              <line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
            </svg>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-gray-400">
            Fields
          </span>
          <span className="text-[10px] font-bold text-brand bg-red-50 px-1.5 py-px rounded">
            {configData?.fields.length || 0}
          </span>
        </div>
        <FieldList fields={configData?.fields || []} />
      </div>
    </aside>
  );
}
