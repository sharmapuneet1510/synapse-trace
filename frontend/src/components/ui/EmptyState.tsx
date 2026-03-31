import React from 'react';
import { GitBranch } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
}

export function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 p-8"
      style={{ color: 'var(--text-muted)' }}>
      <div style={{ opacity: 0.3 }}>{icon || <GitBranch size={40} />}</div>
      <span className="label-heading" style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>{title}</span>
      {description && (
        <p style={{ fontSize: '11px', textAlign: 'center', maxWidth: 300, lineHeight: 1.5 }}>
          {description}
        </p>
      )}
    </div>
  );
}
