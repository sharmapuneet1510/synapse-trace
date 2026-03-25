import { useState } from 'react';
import type { JurisdictionSummary } from '../../types/jurisdiction';

interface Props {
  jurisdictions: JurisdictionSummary[];
  selected: string | null;
  onSelect: (id: string) => void;
}

export default function JurisdictionSelector({ jurisdictions, selected, onSelect }: Props) {
  const [search, setSearch] = useState('');

  const filtered = jurisdictions.filter(
    (j) =>
      j.id.toLowerCase().includes(search.toLowerCase()) ||
      j.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div>
      {/* Search bar for many jurisdictions */}
      {jurisdictions.length > 5 && (
        <div className="relative mb-2">
          <svg className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Filter jurisdictions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-7 pr-3 py-[5px] text-[11px] border border-gray-200 rounded bg-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-brand/20 focus:border-brand/40"
          />
        </div>
      )}

      {/* Grid of jurisdiction cards — 2 cols, scrollable for many */}
      <div
        className="grid grid-cols-2 gap-1.5 overflow-y-auto"
        style={{ maxHeight: jurisdictions.length > 8 ? '140px' : 'none' }}
      >
        {filtered.map((j) => (
          <button
            key={j.id}
            onClick={() => onSelect(j.id)}
            className={`jurisdiction-card ${selected === j.id ? 'active' : ''}`}
          >
            {j.id.toUpperCase()}
          </button>
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="text-[11px] text-gray-400 text-center py-2">No match</div>
      )}
    </div>
  );
}
