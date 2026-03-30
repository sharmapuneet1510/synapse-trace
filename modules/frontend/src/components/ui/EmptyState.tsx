import React from 'react';
import { GitBranch } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
}

export function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-500 p-8">
      <div className="text-slate-600">{icon || <GitBranch size={48} />}</div>
      <p className="text-sm font-semibold text-slate-400">{title}</p>
      {description && <p className="text-xs text-center max-w-xs">{description}</p>}
    </div>
  );
}
