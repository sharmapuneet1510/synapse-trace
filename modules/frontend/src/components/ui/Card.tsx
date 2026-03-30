import React from 'react';

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Card({ title, children, className = '' }: CardProps) {
  return (
    <div className={`bg-slate-800 border border-slate-700 rounded-lg p-4 ${className}`}>
      {title && <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">{title}</h3>}
      {children}
    </div>
  );
}
