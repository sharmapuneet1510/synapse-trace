import { useState } from 'react';
import type { XPathEntry } from '../../types/field';

interface Props {
  xpaths: XPathEntry[];
}

export default function InputXPathsTable({ xpaths }: Props) {
  const [search, setSearch] = useState('');

  const filtered = xpaths.filter(
    (x) =>
      x.name.toLowerCase().includes(search.toLowerCase()) ||
      x.xpath.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="glass-card">
      <div className="section-bar" style={{ borderRadius: '12px 12px 0 0' }}>
        <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
        </svg>
        <span>Input XPaths</span>
        <span className="section-count">({xpaths.length})</span>
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="section-search"
        />
      </div>

      {/* Table header */}
      <div
        className="grid text-[10px] font-bold uppercase tracking-[0.06em] bg-gray-50 text-gray-500 border-b border-gray-100"
        style={{ gridTemplateColumns: '160px 140px 1fr' }}
      >
        <div className="px-4 py-2.5 border-r border-gray-100">Name</div>
        <div className="px-4 py-2.5 border-r border-gray-100">Source</div>
        <div className="px-4 py-2.5">XPath</div>
      </div>

      {/* Table body */}
      <div className="max-h-[320px] overflow-y-auto">
        {filtered.map((x, i) => (
          <div
            key={`${x.xpath}-${i}`}
            className="grid text-[12px] border-b border-gray-50 last:border-0 hover:bg-red-50/30 transition-colors duration-100"
            style={{
              gridTemplateColumns: '160px 140px 1fr',
              background: i % 2 === 1 ? '#fafafa' : '#fff',
            }}
          >
            <div className="px-4 py-[8px] font-medium text-gray-800 truncate border-r border-gray-50">
              {x.name}
            </div>
            <div className="px-4 py-[8px] text-gray-500 truncate font-mono text-[10px] border-r border-gray-50">
              {x.source}
            </div>
            <div
              className="px-4 py-[8px] text-gray-500 font-mono text-[10px] truncate"
              title={x.xpath}
            >
              {x.xpath}
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="px-4 py-8 text-[12px] text-gray-400 text-center">
            {xpaths.length === 0 ? 'No XPaths found' : 'No match'}
          </div>
        )}
      </div>
    </div>
  );
}
