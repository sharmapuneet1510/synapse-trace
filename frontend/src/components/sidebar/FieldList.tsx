import { useState } from 'react';
import { useAppStore } from '../../stores/appStore';
import type { FieldConfig } from '../../types/jurisdiction';

interface Props {
  fields: FieldConfig[];
}

export default function FieldList({ fields }: Props) {
  const { fieldName, setField } = useAppStore();
  const [search, setSearch] = useState('');

  const filtered = fields.filter(
    (f) =>
      f.header.toLowerCase().includes(search.toLowerCase()) ||
      f.field_name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="flex flex-col overflow-hidden flex-1">
      {/* Search */}
      <div className="px-3.5 pb-2">
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search fields..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-[7px] text-[11px] border border-gray-200 rounded-lg bg-gray-50/50 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand/15 focus:border-brand/30 focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* List */}
      <div className="overflow-y-auto flex-1">
        {filtered.map((f, idx) => {
          const isActive = fieldName === f.field_name;
          return (
            <button
              key={f.field_name}
              onClick={() => setField(f.field_name)}
              className="w-full text-left flex items-center gap-2.5 px-3.5 py-[10px] transition-all duration-100 group"
              style={{
                borderLeft: isActive ? '3px solid #dc2626' : '3px solid transparent',
                background: isActive ? 'linear-gradient(90deg, #fef2f2, #fff)' : 'transparent',
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = '#f9fafb';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <span
                className="text-[10px] w-[20px] h-[20px] rounded flex items-center justify-center shrink-0 font-bold tabular-nums"
                style={{
                  background: isActive ? '#dc2626' : '#f3f4f6',
                  color: isActive ? '#fff' : '#9ca3af',
                }}
              >
                {idx + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div
                  className="text-[12px] font-medium truncate leading-tight"
                  style={{ color: isActive ? '#991b1b' : '#374151' }}
                >
                  {f.header}
                </div>
              </div>
              <svg
                className="w-3 h-3 shrink-0 transition-transform duration-100 group-hover:translate-x-0.5"
                style={{ color: isActive ? '#dc2626' : '#d1d5db' }}
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                viewBox="0 0 24 24"
              >
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
          );
        })}
        {filtered.length === 0 && (
          <div className="px-4 py-8 text-[11px] text-gray-400 text-center">
            No fields match your search
          </div>
        )}
      </div>
    </div>
  );
}
