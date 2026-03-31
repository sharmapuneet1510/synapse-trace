import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  type Node, type Edge,
  BackgroundVariant, MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useAppStore } from '../../store/appStore';
import { PipelineNode } from './PipelineNode';
import { Layers } from 'lucide-react';

const NODE_TYPES = { pipelineNode: PipelineNode };
const HORZ_GAP = 290;
const VERT_GAP = 130;

const TYPE_COLORS: Record<string, string> = {
  EXTRACTION:              '#7c3aed',
  MAPPING:                 '#0891b2',
  ENRICHMENT:              '#059669',
  OVERRIDE:                '#d97706',
  DEFAULTING:              '#6b7280',
  PASS_THROUGH:            '#9ca3af',
  CONDITIONAL_ASSIGNMENT:  '#ea580c',
  FINAL_REPORT_ASSIGNMENT: '#dc2626',
};

// ── DAG layout via topological BFS ───────────────────────────────────────────

interface GNode { id: string; label: string; type: string; properties: Record<string, unknown> }
interface GEdge { source: string; target: string; relation: string; properties: Record<string, unknown> }

function computeDagPositions(
  gnodes: GNode[],
  gedges: GEdge[],
): Record<string, { x: number; y: number }> {
  const adj: Record<string, string[]> = {};
  const inDeg: Record<string, number> = {};
  gnodes.forEach((n) => { adj[n.id] = []; inDeg[n.id] = 0; });
  gedges.forEach((e) => {
    if (adj[e.source]) adj[e.source].push(e.target);
    if (inDeg[e.target] !== undefined) inDeg[e.target]++;
  });

  // BFS to assign column (topological level)
  const level: Record<string, number> = {};
  const queue: string[] = gnodes.filter((n) => inDeg[n.id] === 0).map((n) => n.id);
  queue.forEach((id) => (level[id] = 0));

  const bfsQ = [...queue];
  while (bfsQ.length) {
    const id = bfsQ.shift()!;
    for (const next of adj[id] ?? []) {
      level[next] = Math.max(level[next] ?? 0, (level[id] ?? 0) + 1);
      inDeg[next]--;
      if (inDeg[next] <= 0) bfsQ.push(next);
    }
  }

  // Group by column
  const cols: Record<number, string[]> = {};
  gnodes.forEach((n) => {
    const col = level[n.id] ?? 0;
    if (!cols[col]) cols[col] = [];
    cols[col].push(n.id);
  });

  // Assign x/y — nodes in same column stacked vertically, centred
  const positions: Record<string, { x: number; y: number }> = {};
  Object.entries(cols).forEach(([colStr, ids]) => {
    const col = Number(colStr);
    const count = ids.length;
    ids.forEach((id, i) => {
      positions[id] = {
        x: col * HORZ_GAP,
        y: (i - (count - 1) / 2) * VERT_GAP,
      };
    });
  });
  return positions;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function PipelineView() {
  const { traceResult, setSelectedNodeId, selectedNodeId } = useAppStore();

  const { rfNodes, rfEdges } = useMemo(() => {
    if (!traceResult) return { rfNodes: [], rfEdges: [] };

    const gNodes = traceResult.graph_json?.nodes ?? [];
    const gEdges = traceResult.graph_json?.edges ?? [];

    // Build a lookup from graph node id → pipeline step data
    const stepById = Object.fromEntries(
      traceResult.pipeline.map((s) => [s.step_id, s]),
    );

    // Determine positions — prefer DAG layout when graph has fan-out
    let positions: Record<string, { x: number; y: number }>;
    if (gNodes.length > 0) {
      positions = computeDagPositions(gNodes, gEdges);
    } else {
      // Fallback: linear layout from pipeline order
      positions = Object.fromEntries(
        traceResult.pipeline.map((s, i) => [s.step_id, { x: i * HORZ_GAP, y: 0 }]),
      );
    }

    // Build React Flow nodes
    const sourceNodes = gNodes.length > 0 ? gNodes : traceResult.pipeline.map((s) => ({
      id: s.step_id, label: s.label, type: s.type, properties: { transformation_type: s.transformation_type },
    }));

    const nodes: Node[] = sourceNodes.map((gn) => {
      const step = stepById[gn.id];
      const tType = (step?.transformation_type ?? gn.properties?.transformation_type ?? '') as string;
      return {
        id: gn.id,
        type: 'pipelineNode',
        position: positions[gn.id] ?? { x: 0, y: 0 },
        data: {
          label: gn.label,
          node_type: gn.type,
          transformation_type: tType,
          evidence: step?.evidence ?? {},
        },
        selected: gn.id === selectedNodeId,
      };
    });

    // Build React Flow edges from graph_json
    const nodeIds = new Set(nodes.map((n) => n.id));
    const edges: Edge[] = [];

    const sourceEdges = gEdges.length > 0 ? gEdges : traceResult.pipeline.slice(0, -1).map((s, i) => ({
      source: s.step_id,
      target: traceResult.pipeline[i + 1].step_id,
      relation: 'feeds',
      properties: {},
    }));

    sourceEdges.forEach((ge, idx) => {
      if (!nodeIds.has(ge.source) || !nodeIds.has(ge.target)) return;
      const srcStep = stepById[ge.source];
      const tType = (srcStep?.transformation_type ?? '') as string;
      const color = TYPE_COLORS[tType] ?? '#9ca3af';
      const isDashed = ge.relation === 'conditionally_feeds' || ge.relation === 'overrides';
      edges.push({
        id: `e-${idx}-${ge.source}-${ge.target}`,
        source: ge.source,
        target: ge.target,
        label: ge.relation !== 'feeds' ? ge.relation : undefined,
        animated: !isDashed,
        style: {
          stroke: color,
          strokeWidth: isDashed ? 1 : 1.5,
          strokeDasharray: isDashed ? '5 3' : undefined,
          opacity: 0.75,
        },
        labelStyle: { fill: '#9ca3af', fontSize: 8, fontFamily: "'IBM Plex Mono', monospace" },
        markerEnd: { type: MarkerType.ArrowClosed, color, width: 10, height: 10 },
      });
    });

    return { rfNodes: nodes, rfEdges: edges };
  }, [traceResult, selectedNodeId]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id === selectedNodeId ? null : node.id);
    },
    [selectedNodeId, setSelectedNodeId],
  );

  if (!traceResult || rfNodes.length === 0) {
    return (
      <div
        className="w-full h-full flex flex-col items-center justify-center gap-4"
        style={{ color: 'var(--text-muted)' }}
      >
        <Layers size={40} style={{ opacity: 0.3 }} />
        <span className="label-heading" style={{ fontSize: '11px' }}>
          No pipeline data
        </span>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ReactFlow
        key={traceResult.trace_id}
        nodes={rfNodes}
        edges={rfEdges}
        nodeTypes={NODE_TYPES}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.35 }}
        minZoom={0.15}
        maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={28} size={1} color="#d1d5db" />
        <Controls showFitView showZoom showInteractive={false} style={{ bottom: 12, left: 12 }} />
        <MiniMap
          nodeColor={(n) => TYPE_COLORS[(n.data?.transformation_type as string) ?? ''] ?? '#d1d5db'}
          maskColor="rgba(244,245,247,0.7)"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 5,
          }}
        />
      </ReactFlow>
    </div>
  );
}
