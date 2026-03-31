import React from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

export function BranchNode({ data, selected }: NodeProps) {
  const isCentral = data.isCentral as boolean;
  const label = data.label as string;
  const condition = data.condition as string;
  const outcome = data.outcome as string | undefined;

  if (isCentral) {
    return (
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '2px solid var(--amber)',
          borderRadius: '50%',
          minWidth: 110,
          minHeight: 110,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 0 4px var(--amber-glow), 0 4px 16px rgba(0,0,0,0.1)',
          cursor: 'default',
        }}
      >
        <span
          style={{
            color: 'var(--amber)',
            fontFamily: "'IBM Plex Mono', monospace",
            fontWeight: 600,
            fontSize: '12px',
            textAlign: 'center',
            padding: '0 8px',
          }}
        >
          {label}
        </span>
        {[Position.Right, Position.Left, Position.Top, Position.Bottom].map((pos, i) => (
          <Handle
            key={i}
            type="source"
            position={pos}
            id={pos}
            style={{ background: 'var(--amber)', width: 6, height: 6, border: 'none' }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: selected ? '1.5px solid var(--coral)' : '1px solid var(--border)',
        borderLeft: '3px solid var(--coral)',
        borderRadius: 5,
        minWidth: 155,
        maxWidth: 210,
        boxShadow: selected
          ? '0 0 0 3px rgba(234,88,12,0.15), 0 4px 12px rgba(0,0,0,0.1)'
          : '0 1px 4px rgba(0,0,0,0.08)',
        overflow: 'hidden',
        transition: 'all 0.15s',
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: 'var(--coral)', width: 6, height: 6, border: 'none', left: -3 }}
      />

      <div style={{ height: 1.5, background: 'var(--coral)', opacity: selected ? 1 : 0.4 }} />

      <div style={{ padding: '8px 10px' }}>
        <span className="label-tag" style={{ color: 'var(--coral)', fontSize: '9px' }}>CONDITION</span>
        <div
          style={{
            color: selected ? '#111827' : 'var(--text-secondary)',
            fontSize: '10px',
            fontFamily: "'IBM Plex Mono', monospace",
            lineHeight: 1.4,
            marginTop: 4,
            wordBreak: 'break-word',
          }}
        >
          {condition}
        </div>
        {outcome && (
          <div
            style={{
              marginTop: 6,
              fontSize: '9px',
              color: 'var(--emerald)',
              fontFamily: "'IBM Plex Mono', monospace",
              lineHeight: 1.4,
            }}
          >
            → {outcome}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: 'var(--coral)', width: 6, height: 6, border: 'none', right: -3 }}
      />
    </div>
  );
}
