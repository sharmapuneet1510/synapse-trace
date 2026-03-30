import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  type Node, type Edge, useNodesState, useEdgesState,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useAppStore } from '../../store/appStore';
import { PipelineNode } from './PipelineNode';
import { EmptyState } from '../../components/ui/EmptyState';
import { Layers } from 'lucide-react';

const NODE_TYPES = { pipelineNode: PipelineNode };
const HORZ_GAP = 260;
const VERT_GAP = 80;

export function PipelineView() {
  const { traceResult, setSelectedNodeId, selectedNodeId } = useAppStore();

  const { nodes: rfNodes, edges: rfEdges } = useMemo(() => {
    if (!traceResult) return { nodes: [], edges: [] };

    const steps = traceResult.pipeline;
    const nodes: Node[] = steps.map((step, i) => ({
      id: step.step_id,
      type: 'pipelineNode',
      position: { x: i * HORZ_GAP, y: 0 },
      data: {
        label: step.label,
        node_type: step.type,
        transformation_type: step.transformation_type,
        evidence: step.evidence || {},
      },
      selected: step.step_id === selectedNodeId,
    }));

    const edges: Edge[] = [];
    for (let i = 0; i < steps.length - 1; i++) {
      edges.push({
        id: `e-${i}`,
        source: steps[i].step_id,
        target: steps[i + 1].step_id,
        animated: false,
        style: { stroke: '#475569' },
        labelStyle: { fill: '#94a3b8', fontSize: 10 },
      });
    }

    // Also add graph edges
    if (traceResult.graph_json?.edges) {
      for (const e of traceResult.graph_json.edges) {
        const existingEdge = edges.find((ex) => ex.source === e.source && ex.target === e.target);
        if (!existingEdge && nodes.find((n) => n.id === e.source) && nodes.find((n) => n.id === e.target)) {
          edges.push({
            id: `ge-${e.source}-${e.target}`,
            source: e.source,
            target: e.target,
            label: e.relation,
            style: { stroke: '#334155', strokeDasharray: '4 2' },
            labelStyle: { fill: '#64748b', fontSize: 9 },
          });
        }
      }
    }

    return { nodes, edges };
  }, [traceResult, selectedNodeId]);

  const [nodes, , onNodesChange] = useNodesState(rfNodes);
  const [edges, , onEdgesChange] = useEdgesState(rfEdges);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id === selectedNodeId ? null : node.id);
  }, [selectedNodeId, setSelectedNodeId]);

  if (!traceResult || rfNodes.length === 0) {
    return (
      <EmptyState
        icon={<Layers size={48} />}
        title="No pipeline data"
        description="Run a trace to see the field transformation pipeline"
      />
    );
  }

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        nodeTypes={NODE_TYPES}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.3}
        maxZoom={2}
        attributionPosition="bottom-right"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1e293b" />
        <Controls />
        <MiniMap
          nodeColor={(n) => {
            const t = (n.data?.transformation_type as string) || '';
            const colors: Record<string, string> = {
              EXTRACTION: '#3b82f6', MAPPING: '#8b5cf6', ENRICHMENT: '#10b981',
              OVERRIDE: '#f59e0b', FINAL_REPORT_ASSIGNMENT: '#ef4444',
              CONDITIONAL_ASSIGNMENT: '#eab308',
            };
            return colors[t] || '#334155';
          }}
          maskColor="rgba(15,23,42,0.7)"
        />
      </ReactFlow>
    </div>
  );
}
