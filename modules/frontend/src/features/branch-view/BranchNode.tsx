import React from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

export function BranchNode({ data, selected }: NodeProps) {
  const isCentral = data.isCentral as boolean;
  const label = data.label as string;
  const condition = data.condition as string;
  const outcome = data.outcome as string | undefined;

  if (isCentral) {
    return (
      <div className="bg-blue-900/60 border-2 border-blue-500 rounded-full px-4 py-2 text-sm font-bold text-blue-200 text-center min-w-[120px]">
        {label}
        <Handle type="source" position={Position.Right} className="!bg-blue-500 !w-2 !h-2" />
        <Handle type="source" position={Position.Left} className="!bg-blue-500 !w-2 !h-2" id="left" />
        <Handle type="source" position={Position.Top} className="!bg-blue-500 !w-2 !h-2" id="top" />
        <Handle type="source" position={Position.Bottom} className="!bg-blue-500 !w-2 !h-2" id="bottom" />
      </div>
    );
  }

  return (
    <div
      className={`bg-slate-800 border rounded-lg px-3 py-2 min-w-[140px] max-w-[200px] ${
        selected ? 'border-yellow-500' : 'border-slate-600'
      }`}
    >
      <Handle type="target" position={Position.Left} className="!bg-slate-500 !w-2 !h-2" />
      <div className="text-[10px] text-slate-500 mb-1">Condition:</div>
      <div className="text-xs text-yellow-300 font-mono leading-tight">{condition}</div>
      {outcome && (
        <div className="mt-1.5 text-[10px] text-emerald-400 font-semibold">→ {outcome}</div>
      )}
      <Handle type="source" position={Position.Right} className="!bg-slate-500 !w-2 !h-2" />
    </div>
  );
}
