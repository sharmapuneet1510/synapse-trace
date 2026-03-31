import React, { useMemo } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  type Node, type Edge, BackgroundVariant,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useAppStore } from '../../store/appStore';
import { BranchNode } from './BranchNode';
import { Network } from 'lucide-react';

const NODE_TYPES = { branchNode: BranchNode };

export function BranchView() {
  const { traceResult, setSelectedNodeId, selectedNodeId } = useAppStore();

  const { nodes, edges } = useMemo(() => {
    if (!traceResult) return { nodes: [], edges: [] };

    const branches = traceResult.branches;
    const rfNodes: Node[] = [];
    const rfEdges: Edge[] = [];

    rfNodes.push({
      id: 'center',
      type: 'branchNode',
      position: { x: 0, y: 0 },
      data: { isCentral: true, label: traceResult.field_name },
    });

    const angleStep = (2 * Math.PI) / Math.max(branches.length, 1);
    const radius = 240;

    branches.forEach((branch, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      rfNodes.push({
        id: branch.branch_id,
        type: 'branchNode',
        position: { x, y },
        data: {
          isCentral: false,
          label: branch.branch_id,
          condition: branch.condition,
          outcome: branch.outcome,
        },
        selected: branch.branch_id === selectedNodeId,
      });

      const cond = branch.condition;
      const shortCond = cond.length > 36 ? cond.slice(0, 36) + '…' : cond;

      rfEdges.push({
        id: `e-center-${branch.branch_id}`,
        source: 'center',
        target: branch.branch_id,
        label: shortCond,
        animated: true,
        style: { stroke: '#253550', strokeWidth: 1.5 },
        labelStyle: { fill: '#3d5275', fontSize: 9, fontFamily: "'IBM Plex Mono', monospace" },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#253550', width: 8, height: 8 },
      });
    });

    return { nodes: rfNodes, edges: rfEdges };
  }, [traceResult, selectedNodeId]);

  if (!traceResult || traceResult.branches.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-4"
        style={{ color: 'var(--text-muted)' }}>
        <Network size={40} style={{ opacity: 0.3 }} />
        <span className="label-heading" style={{ fontSize: '11px' }}>No branch data</span>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Trace a field with conditional logic to see branch analysis
        </span>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ReactFlow
        key={traceResult.trace_id}
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        onNodeClick={(_, n) => setSelectedNodeId(n.id === selectedNodeId ? null : n.id)}
        fitView
        fitViewOptions={{ padding: 0.5 }}
        minZoom={0.2}
        maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={28} size={1} color="#d1d5db" />
        <Controls style={{ bottom: 12, left: 12 }} showInteractive={false} />
        <MiniMap
          maskColor="rgba(5,8,15,0.75)"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 5 }}
        />
      </ReactFlow>
    </div>
  );
}
