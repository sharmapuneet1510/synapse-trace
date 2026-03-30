import React from 'react';
import type { TransformationType, OriginType } from '../../types/trace';

const TYPE_STYLES: Record<string, string> = {
  EXTRACTION: 'bg-blue-900/60 text-blue-300 border-blue-700',
  MAPPING: 'bg-purple-900/60 text-purple-300 border-purple-700',
  ENRICHMENT: 'bg-emerald-900/60 text-emerald-300 border-emerald-700',
  OVERRIDE: 'bg-orange-900/60 text-orange-300 border-orange-700',
  DEFAULTING: 'bg-slate-700/60 text-slate-300 border-slate-600',
  PASS_THROUGH: 'bg-slate-800/60 text-slate-400 border-slate-600',
  CONDITIONAL_ASSIGNMENT: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
  FINAL_REPORT_ASSIGNMENT: 'bg-red-900/60 text-red-300 border-red-700',
  XSLT: 'bg-teal-900/60 text-teal-300 border-teal-700',
  JAVA: 'bg-indigo-900/60 text-indigo-300 border-indigo-700',
  XSLT_THEN_JAVA: 'bg-violet-900/60 text-violet-300 border-violet-700',
  UNKNOWN: 'bg-slate-800/60 text-slate-400 border-slate-600',
};

interface BadgeProps {
  label: string;
  className?: string;
}

export function Badge({ label, className = '' }: BadgeProps) {
  const style = TYPE_STYLES[label] || 'bg-slate-700/60 text-slate-300 border-slate-600';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${style} ${className}`}>
      {label}
    </span>
  );
}
