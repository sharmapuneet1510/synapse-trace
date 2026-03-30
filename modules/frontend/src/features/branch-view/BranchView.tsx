import React, { useMemo } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  type Node, type Edge, BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useAppStore } from '../../store/appStore';
import { BranchNode } from './BranchNode';
import { EmptyState } from '../../components/ui/EmptyState';
import { Network } from 'lucide-react';

const NODE_TYPES = { branchNode: BranchNode };

export function BranchView() {
  const { traceResult, setSelectedNodeId, selectedNodeId } = useAppStore();

  const { nodes, edges } = useMemo(() => {
    if (!traceResult) return { nodes: [], edges: [] };

    const branches = traceResult.branches;
    const rfNodes: Node[] = [];
    const rfEdges: Edge[] = [];

    // Central node
    rfNodes.push({
      id: 'center',
      type: 'branchNode',
      position: { x: 0, y: 0 },
      data: { isCentral: true, label: traceResult.field_name },
    });

    const angleStep = (2 * Math.PI) / Math.max(branches.length, 1);
    const radius = 220;

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

      rfEdges.push({
        id: `e-center-${branch.branch_id}`,
        source: 'center',
        target: branch.branch_id,
        label: branch.condition.length > 40 ? branch.condition.slice(0, 40) + '…' : branch.condition,
        style: { stroke: '#475569' },
        labelStyle: { fill: '#94a3b8', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' },
        animated: true,
      });
    });

    return { nodes: rfNodes, edges: rfEdges };
  }, [traceResult, selectedNodeId]);

  if (!traceResult || traceResult.branches.length === 0) {
    return (
      <EmptyState
        icon={<Network size={48} />}
        title="No branch data"
        description="Trace a field with conditional logic to see branch analysis"
      />
    );
  }

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        onNodeClick={(_, n) => setSelectedNodeId(n.id === selectedNodeId ? null : n.id)}
        fitView
        fitViewOptions={{ padding: 0.4 }}
        minZoom={0.2}
        maxZoom={2}
        attributionPosition="bottom-right"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1e293b" />
        <Controls />
        <MiniMap maskColor="rgba(15,23,42,0.7)" />
      </ReactFlow>
    </div>
  );
}
