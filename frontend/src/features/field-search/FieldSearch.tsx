import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Zap, ChevronDown, X, Search } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { traceApi } from '../../api/traceApi';
import {
  JURISDICTIONS,
  FIELD_TYPES,
  JURISDICTION_CONFIG,
  getFieldsForSelection,
} from '../../data/jurisdictionConfig';
import { FIELD_DUMMY_MAP } from '../../data/dummyData';

// ── Searchable multi-select dropdown ─────────────────────────────────────────

interface MultiSelectProps {
  options: string[];
  value: string[];
  onChange: (v: string[]) => void;
  placeholder: string;
  required?: boolean;
  disabled?: boolean;
  badge?: string; // e.g. count label
}

function SearchableMultiSelect({
  options,
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
}: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch('');
      }
    }
    document.addEventListener('mousedown', onOutside);
    return () => document.removeEventListener('mousedown', onOutside);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 30);
  }, [open]);

  const filtered = useMemo(
    () => options.filter((o) => o.toLowerCase().includes(search.toLowerCase())),
    [options, search],
  );

  const toggle = (opt: string) => {
    onChange(value.includes(opt) ? value.filter((v) => v !== opt) : [...value, opt]);
  };

  const displayLabel = () => {
    if (value.length === 0) return placeholder;
    if (value.length === 1) return value[0];
    return `${value[0]} +${value.length - 1} more`;
  };

  const isEmpty = required && value.length === 0;

  return (
    <div className="relative" ref={ref}>
      {/* Trigger */}
      <button
        type="button"
        onClick={() => !disabled && setOpen((o) => !o)}
        style={{
          width: '100%',
          background: 'var(--bg-elevated)',
          border: `1px solid ${
            open ? 'var(--amber)' : isEmpty ? 'rgba(220,38,38,0.45)' : 'var(--border-bright)'
          }`,
          borderRadius: 4,
          padding: '6px 8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 6,
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.35 : 1,
          transition: 'border-color 0.15s',
          boxShadow: open ? '0 0 0 2px var(--amber-glow)' : 'none',
        }}
      >
        <span
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: '11px',
            color: value.length > 0 ? 'var(--text-primary)' : 'var(--text-muted)',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            textAlign: 'left',
          }}
        >
          {displayLabel()}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}>
          {value.length > 0 && (
            <span
              style={{
                background: 'var(--amber)',
                color: '#fff',
                borderRadius: 3,
                padding: '1px 5px',
                fontSize: '9px',
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 700,
                letterSpacing: '0.05em',
              }}
            >
              {value.length}
            </span>
          )}
          <ChevronDown
            size={10}
            style={{
              color: 'var(--text-muted)',
              transform: open ? 'rotate(180deg)' : 'none',
              transition: 'transform 0.15s',
            }}
          />
        </div>
      </button>

      {/* Dropdown */}
      {open && !disabled && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: 0,
            right: 0,
            zIndex: 200,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-bright)',
            borderRadius: 4,
            boxShadow: '0 12px 40px rgba(0,0,0,0.55)',
            overflow: 'hidden',
          }}
        >
          {/* Search input */}
          <div
            style={{
              padding: '6px 8px',
              borderBottom: '1px solid var(--border)',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Search
              size={10}
              style={{ color: 'var(--text-muted)', position: 'absolute', left: 16 }}
            />
            <input
              ref={inputRef}
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              style={{
                width: '100%',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 3,
                padding: '4px 8px 4px 24px',
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: '10px',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
          </div>

          {/* Select all / clear bar */}
          {filtered.length > 0 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '4px 10px',
                borderBottom: '1px solid var(--border)',
                background: 'rgba(255,255,255,0.02)',
              }}
            >
              <button
                type="button"
                onClick={() => {
                  const next = Array.from(new Set([...value, ...filtered]));
                  onChange(next);
                }}
                style={{
                  fontSize: '9px',
                  color: 'var(--amber)',
                  fontFamily: "'Barlow Condensed', sans-serif",
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  cursor: 'pointer',
                  background: 'none',
                  border: 'none',
                  padding: 0,
                }}
              >
                SELECT ALL
              </button>
              {value.length > 0 && (
                <button
                  type="button"
                  onClick={() => onChange([])}
                  style={{
                    fontSize: '9px',
                    color: 'var(--text-muted)',
                    fontFamily: "'Barlow Condensed', sans-serif",
                    fontWeight: 700,
                    letterSpacing: '0.08em',
                    cursor: 'pointer',
                    background: 'none',
                    border: 'none',
                    padding: 0,
                  }}
                >
                  CLEAR
                </button>
              )}
            </div>
          )}

          {/* Options list */}
          <div style={{ maxHeight: 200, overflowY: 'auto' }}>
            {filtered.length === 0 ? (
              <div
                style={{
                  padding: '14px 10px',
                  color: 'var(--text-muted)',
                  fontSize: '10px',
                  fontFamily: "'IBM Plex Mono', monospace",
                  textAlign: 'center',
                }}
              >
                No matches
              </div>
            ) : (
              filtered.map((opt) => {
                const selected = value.includes(opt);
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => toggle(opt)}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '7px 10px',
                      background: selected ? 'rgba(220,38,38,0.09)' : 'transparent',
                      border: 'none',
                      borderLeft: selected ? '2px solid var(--amber)' : '2px solid transparent',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'background 0.1s',
                    }}
                    onMouseEnter={(e) => {
                      if (!selected)
                        (e.currentTarget as HTMLButtonElement).style.background =
                          'rgba(255,255,255,0.04)';
                    }}
                    onMouseLeave={(e) => {
                      if (!selected)
                        (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
                    }}
                  >
                    {/* Checkbox */}
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        border: `1px solid ${selected ? 'var(--amber)' : 'var(--border-bright)'}`,
                        borderRadius: 2,
                        background: selected ? 'var(--amber)' : 'transparent',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        transition: 'all 0.1s',
                      }}
                    >
                      {selected && (
                        <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                          <path
                            d="M1.5 4L3.5 6L6.5 2"
                            stroke="white"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      )}
                    </div>
                    <span
                      style={{
                        fontFamily: "'IBM Plex Mono', monospace",
                        fontSize: '10px',
                        color: selected ? 'var(--text-primary)' : 'var(--text-secondary)',
                        fontWeight: selected ? 500 : 400,
                        flex: 1,
                      }}
                    >
                      {opt}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── FieldSearch main component ────────────────────────────────────────────────

export function FieldSearch() {
  const {
    setFieldName,
    setJurisdiction,
    isTracing,
    setTracing,
    setTraceResult,
    setTraceError,
    addRecentTrace,
    addLogs,
    traceError,
    selectedJurisdictions,
    setSelectedJurisdictions,
    selectedFieldTypes,
    setSelectedFieldTypes,
    selectedFields,
    setSelectedFields,
  } = useAppStore();

  // Available field types based on selected jurisdictions
  const availableFieldTypes = useMemo<string[]>(() => {
    if (selectedJurisdictions.length === 0) return [...FIELD_TYPES];
    const types = new Set<string>();
    for (const jur of selectedJurisdictions) {
      Object.keys(JURISDICTION_CONFIG[jur] ?? {}).forEach((t) => types.add(t));
    }
    return Array.from(types);
  }, [selectedJurisdictions]);

  // Available fields based on jurisdiction + field type selection
  const availableFields = useMemo(
    () => getFieldsForSelection(selectedJurisdictions, selectedFieldTypes),
    [selectedJurisdictions, selectedFieldTypes],
  );

  // Drop fields no longer available when jurisdiction/type changes
  useEffect(() => {
    if (availableFields.length === 0) return;
    const valid = selectedFields.filter((f) => availableFields.includes(f));
    if (valid.length !== selectedFields.length) setSelectedFields(valid);
  }, [availableFields]);

  const isValid = selectedJurisdictions.length > 0 && selectedFields.length > 0;

  const handleTrace = async () => {
    if (!isValid) return;
    const field = selectedFields[0];
    const jur = selectedJurisdictions[0];
    setFieldName(field);
    setJurisdiction(jur);
    setTracing(true);
    try {
      const result = await traceApi.traceField({
        field_name: field,
        jurisdiction: jur,
        max_depth: 20,
        enable_condition_tracing: true,
        enable_xslt_imports: true,
      });
      setTraceResult(result);
      addRecentTrace(field);
      try {
        const logs = await traceApi.getLogs(result.trace_id);
        if (Array.isArray(logs)) addLogs(logs);
      } catch {
        /* optional */
      }
    } catch (err: unknown) {
      // Fall back to local dummy data if backend is unavailable
      const fallback = FIELD_DUMMY_MAP[field.toUpperCase()];
      if (fallback) {
        setTraceResult(fallback);
        addRecentTrace(field);
      } else {
        const msg = err instanceof Error ? err.message : 'Trace failed';
        setTraceError(msg);
      }
    }
  };

  return (
    <div className="flex flex-col gap-3">

      {/* ── Jurisdiction (required) ─────────────────────────────────────────── */}
      <div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 6 }}>
          <span className="label-heading" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
            Jurisdiction
          </span>
          <span style={{ color: 'var(--amber)', fontSize: '10px', lineHeight: 1 }}>*</span>
        </label>
        <SearchableMultiSelect
          options={JURISDICTIONS}
          value={selectedJurisdictions}
          onChange={setSelectedJurisdictions}
          placeholder="Select jurisdiction..."
          required
        />
      </div>

      {/* ── Report type ─────────────────────────────────────────────────────── */}
      <div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 6 }}>
          <span className="label-heading" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
            Report Type
          </span>
        </label>
        <SearchableMultiSelect
          options={availableFieldTypes}
          value={selectedFieldTypes}
          onChange={setSelectedFieldTypes}
          placeholder="All types (TradeState + Valuation)"
          disabled={selectedJurisdictions.length === 0}
        />
      </div>

      {/* ── Field (required) ────────────────────────────────────────────────── */}
      <div>
        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            marginBottom: 6,
          }}
        >
          <span className="label-heading" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
            Field
          </span>
          <span style={{ color: 'var(--amber)', fontSize: '10px', lineHeight: 1 }}>*</span>
          {availableFields.length > 0 && (
            <span
              style={{
                marginLeft: 'auto',
                color: 'var(--text-muted)',
                fontSize: '9px',
                fontFamily: "'IBM Plex Mono', monospace",
              }}
            >
              {availableFields.length} available
            </span>
          )}
        </label>
        <SearchableMultiSelect
          options={availableFields}
          value={selectedFields}
          onChange={setSelectedFields}
          placeholder={
            selectedJurisdictions.length === 0
              ? 'Select jurisdiction first'
              : 'Search & select fields…'
          }
          required
          disabled={selectedJurisdictions.length === 0}
        />
      </div>

      {/* ── Selected fields chips ────────────────────────────────────────────── */}
      {selectedFields.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {selectedFields.map((f) => (
            <div
              key={f}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                background: 'rgba(220,38,38,0.08)',
                border: '1px solid rgba(220,38,38,0.22)',
                borderRadius: 3,
                padding: '2px 6px',
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: '9px',
                color: 'var(--text-primary)',
              }}
            >
              {f}
              <button
                type="button"
                onClick={() => setSelectedFields(selectedFields.filter((sf) => sf !== f))}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  lineHeight: 1,
                }}
              >
                <X size={8} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ── Trace button ─────────────────────────────────────────────────────── */}
      <button
        onClick={handleTrace}
        disabled={isTracing || !isValid}
        className="st-btn-primary w-full justify-center"
        style={{
          marginTop: 2,
          opacity: isTracing || !isValid ? 0.4 : 1,
          cursor: isTracing || !isValid ? 'not-allowed' : 'pointer',
        }}
      >
        {isTracing ? (
          <>
            <span
              style={{
                display: 'inline-block',
                width: 11,
                height: 11,
                borderRadius: '50%',
                border: '1.5px solid rgba(255,255,255,0.6)',
                borderTopColor: '#fff',
                animation: 'spin 0.7s linear infinite',
              }}
            />
            TRACING…
          </>
        ) : (
          <>
            <Zap size={12} /> TRACE FIELD
          </>
        )}
      </button>

      {!isValid && !isTracing && (
        <p
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: '9px',
            color: 'var(--text-muted)',
            margin: 0,
            textAlign: 'center',
          }}
        >
          {selectedJurisdictions.length === 0
            ? 'Select a jurisdiction to begin'
            : 'Select at least one field'}
        </p>
      )}

      {/* ── Error ────────────────────────────────────────────────────────────── */}
      {traceError && (
        <div
          style={{
            background: 'rgba(220,38,38,0.07)',
            border: '1px solid rgba(220,38,38,0.28)',
            borderRadius: 4,
            padding: '8px 10px',
            color: 'var(--red)',
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: '10px',
            lineHeight: 1.5,
          }}
        >
          {traceError}
        </div>
      )}
    </div>
  );
}
