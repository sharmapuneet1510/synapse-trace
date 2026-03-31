import React from 'react';

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  accentColor?: string;
}

export function Card({ title, children, className = '', accentColor }: CardProps) {
  return (
    <div
      className={className}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderTop: accentColor ? `2px solid ${accentColor}` : undefined,
        borderRadius: 5,
        padding: '10px 12px',
      }}
    >
      {title && (
        <div
          className="label-heading mb-2"
          style={{ color: accentColor || 'var(--text-muted)', fontSize: '9px' }}
        >
          {title}
        </div>
      )}
      {children}
    </div>
  );
}
