import React from 'react';

const SIZES = { sm: 14, md: 20, lg: 32 };

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const px = SIZES[size];
  return (
    <div
      className="animate-spin"
      style={{
        width: px,
        height: px,
        border: '1.5px solid var(--border-bright)',
        borderTopColor: 'var(--amber)',
        borderRadius: '50%',
        flexShrink: 0,
      }}
    />
  );
}
