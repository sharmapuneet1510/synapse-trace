import React from 'react';

const PRESET: Record<string, { color: string; bg: string; border: string }> = {
  XSLT:                    { color: '#a78bfa', bg: 'rgba(167,139,250,0.1)',  border: 'rgba(167,139,250,0.25)' },
  JAVA:                    { color: '#22d3ee', bg: 'rgba(34,211,238,0.08)',  border: 'rgba(34,211,238,0.2)' },
  XSLT_THEN_JAVA:          { color: '#f5a623', bg: 'rgba(245,166,35,0.1)',   border: 'rgba(245,166,35,0.25)' },
  EXTRACTION:              { color: '#a78bfa', bg: 'rgba(167,139,250,0.08)', border: 'rgba(167,139,250,0.2)' },
  MAPPING:                 { color: '#22d3ee', bg: 'rgba(34,211,238,0.06)',  border: 'rgba(34,211,238,0.18)' },
  ENRICHMENT:              { color: '#10b981', bg: 'rgba(16,185,129,0.08)',  border: 'rgba(16,185,129,0.2)' },
  OVERRIDE:                { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)',  border: 'rgba(245,158,11,0.2)' },
  DEFAULTING:              { color: '#64748b', bg: 'rgba(100,116,139,0.08)', border: 'rgba(100,116,139,0.2)' },
  PASS_THROUGH:            { color: '#475569', bg: 'rgba(71,85,105,0.08)',   border: 'rgba(71,85,105,0.2)' },
  CONDITIONAL_ASSIGNMENT:  { color: '#ff6b35', bg: 'rgba(255,107,53,0.08)', border: 'rgba(255,107,53,0.2)' },
  FINAL_REPORT_ASSIGNMENT: { color: '#f87171', bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.2)' },
  UNKNOWN:                 { color: '#3d5275', bg: 'rgba(61,82,117,0.08)',   border: 'rgba(61,82,117,0.2)' },
};
const DEFAULT_CFG = { color: '#8b9dc3', bg: 'rgba(139,157,195,0.06)', border: 'rgba(139,157,195,0.18)' };

interface BadgeProps {
  label: string;
  className?: string;
}

export function Badge({ label, className = '' }: BadgeProps) {
  const cfg = PRESET[label.toUpperCase()] || DEFAULT_CFG;
  return (
    <span
      className={`label-tag px-1.5 py-0.5 rounded ${className}`}
      style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`, display: 'inline-block' }}
    >
      {label}
    </span>
  );
}
