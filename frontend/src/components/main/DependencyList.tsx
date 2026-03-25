import { useState } from 'react';
import type { DependencyRef } from '../../types/field';

interface Props {
  dependencies: DependencyRef[];
}

const ICON_MAP: Record<string, string> = {
  DERIVED_FROM: 'triangle',
  CALLS: 'circle',
  TRANSFORMS: 'diamond',
  CROSS_REPO: 'hexagon',
  LOADS_XSLT: 'star',
  UNMARSHALS_TO: 'square',
};

function getIconClass(relationship: string): string {
  return ICON_MAP[relationship] || 'circle';
}

export default function DependencyList({ dependencies }: Props) {
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(true);

  const filtered = dependencies.filter((d) =>
    d.field_name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="glass-card">
      <div
        className="section-bar cursor-pointer"
        style={{ borderRadius: expanded ? '12px 12px 0 0' : '12px' }}
        onClick={() => setExpanded(!expanded)}
      >
        <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
        </svg>
        <span>Dependencies</span>
        <span className="section-count">({dependencies.length})</span>

        <svg
          className="transition-transform duration-200"
          style={{ width: 12, height: 12, transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
          fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>

        {expanded && (
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => { e.stopPropagation(); setSearch(e.target.value); }}
            onClick={(e) => e.stopPropagation()}
            className="section-search"
          />
        )}
      </div>

      {expanded && (
        <div className="bg-white divide-y divide-gray-50 max-h-[280px] overflow-y-auto">
          {filtered.map((dep, i) => {
            const iconType = getIconClass(dep.relationship);
            return (
              <div
                key={`${dep.field_name}-${i}`}
                className="flex items-center gap-3 px-4 py-[10px] hover:bg-gray-50/80 transition-colors duration-100"
              >
                <span className="text-[10px] text-gray-400 w-[18px] text-right tabular-nums">{i + 1}</span>
                <div className="dep-icon">
                  <div className={`dep-icon-${iconType}`} />
                </div>
                <span className="text-[12.5px] font-medium text-gray-800 flex-1">{dep.field_name}</span>
                <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 tracking-tight">
                  {dep.relationship}
                </span>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="px-4 py-8 text-[12px] text-gray-400 text-center">
              {dependencies.length === 0 ? 'No dependencies found' : 'No match'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
