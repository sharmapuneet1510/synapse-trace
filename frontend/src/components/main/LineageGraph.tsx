/**
 * LineageGraph — SVG-based force-directed lineage graph.
 * Shows the subgraph for a traced variable including all its name variations.
 * Uses a simple iterative force layout (no D3 dependency).
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import type { TraceNode, TraceEdge, TraceResponse } from '../../types/trace';

// ── Node type colour map ────────────────────────────────────────────────────
const NODE_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  JAVA_CLASS:    { fill: '#fff7ed', stroke: '#c2410c', text: '#9a3412' },
  JAVA_METHOD:   { fill: '#fef3c7', stroke: '#d97706', text: '#92400e' },
  JAVA_FIELD:    { fill: '#fef2f2', stroke: '#dc2626', text: '#991b1b' },
  JAVA_CONSTANT: { fill: '#fdf4ff', stroke: '#9333ea', text: '#6b21a8' },
  DTO:           { fill: '#f0fdf4', stroke: '#16a34a', text: '#14532d' },
  XSLT_FILE:     { fill: '#eff6ff', stroke: '#2563eb', text: '#1e40af' },
  XSLT_TEMPLATE: { fill: '#f0f9ff', stroke: '#0891b2', text: '#155e75' },
  XSLT_FIELD:    { fill: '#fafafe', stroke: '#6366f1', text: '#3730a3' },
};

const EDGE_COLORS: Record<string, string> = {
  DERIVED_FROM:  '#b91c1c',
  CALLS:         '#2563eb',
  TRANSFORMS:    '#d97706',
  UNMARSHALS_TO: '#059669',
  CROSS_REPO:    '#7c3aed',
  LOADS_XSLT:    '#0891b2',
};

// ── Force layout ────────────────────────────────────────────────────────────

interface Pos { x: number; y: number }

function buildLayout(nodes: TraceNode[], edges: TraceEdge[], w: number, h: number): Map<string, Pos> {
  const pos = new Map<string, Pos>();
  const cx = w / 2, cy = h / 2;

  // Place nodes in a rough circle to start
  nodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length;
    const r = Math.min(w, h) * 0.35;
    pos.set(n.id, { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) });
  });

  const ITERS = 200;
  const K = Math.sqrt((w * h) / Math.max(nodes.length, 1)) * 0.8;
  const REPEL = K * K;
  const ATTRACT = K;

  for (let iter = 0; iter < ITERS; iter++) {
    const disp = new Map<string, Pos>();
    nodes.forEach((n) => disp.set(n.id, { x: 0, y: 0 }));

    // Repulsion between every pair
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = pos.get(nodes[i].id)!;
        const b = pos.get(nodes[j].id)!;
        let dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = REPEL / dist;
        dx = (dx / dist) * force;
        dy = (dy / dist) * force;
        const da = disp.get(nodes[i].id)!;
        const db = disp.get(nodes[j].id)!;
        da.x += dx; da.y += dy;
        db.x -= dx; db.y -= dy;
      }
    }

    // Attraction along edges
    for (const edge of edges) {
      const a = pos.get(edge.source), b = pos.get(edge.target);
      if (!a || !b) continue;
      let dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist * dist) / ATTRACT;
      dx = (dx / dist) * force;
      dy = (dy / dist) * force;
      const da = disp.get(edge.source)!, db = disp.get(edge.target)!;
      da.x += dx; da.y += dy;
      db.x -= dx; db.y -= dy;
    }

    // Apply displacement with cooling
    const temp = Math.max(1, 10 * (1 - iter / ITERS));
    for (const n of nodes) {
      const d = disp.get(n.id)!;
      const p = pos.get(n.id)!;
      const dlen = Math.sqrt(d.x * d.x + d.y * d.y) || 1;
      const step = Math.min(dlen, temp);
      p.x = Math.max(60, Math.min(w - 60, p.x + (d.x / dlen) * step));
      p.y = Math.max(30, Math.min(h - 30, p.y + (d.y / dlen) * step));
    }
  }

  return pos;
}

// ── Component ───────────────────────────────────────────────────────────────

interface Props {
  data: TraceResponse;
  height?: number;
}

export default function LineageGraph({ data, height = 500 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dims, setDims] = useState({ w: 800, h: height });
  const [pos, setPos] = useState<Map<string, Pos>>(new Map());
  const [selected, setSelected] = useState<TraceNode | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const dragging = useRef<{ id: string; ox: number; oy: number } | null>(null);
  const panning = useRef<{ ox: number; oy: number; px: number; py: number } | null>(null);

  // Measure container width
  useEffect(() => {
    const el = svgRef.current?.parentElement;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      const w = entries[0].contentRect.width;
      setDims({ w, h: height });
    });
    obs.observe(el);
    setDims({ w: el.clientWidth, h: height });
    return () => obs.disconnect();
  }, [height]);

  // Recompute layout whenever nodes/edges or dims change
  useEffect(() => {
    if (data.nodes.length === 0) return;
    const layout = buildLayout(data.nodes, data.edges, dims.w, dims.h);
    setPos(layout);
    setPan({ x: 0, y: 0 });
    setZoom(1);
  }, [data.nodes, data.edges, dims.w, dims.h]);

  // ── Drag node ────────────────────────────────────────────────────────────
  const onNodeMouseDown = useCallback((e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const p = pos.get(id)!;
    dragging.current = { id, ox: e.clientX - p.x * zoom, oy: e.clientY - p.y * zoom };
  }, [pos, zoom]);

  // ── Pan ──────────────────────────────────────────────────────────────────
  const onSvgMouseDown = useCallback((e: React.MouseEvent) => {
    panning.current = { ox: e.clientX, oy: e.clientY, px: pan.x, py: pan.y };
  }, [pan]);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragging.current) {
      const { id, ox, oy } = dragging.current;
      setPos((prev) => {
        const next = new Map(prev);
        next.set(id, { x: (e.clientX - ox) / zoom, y: (e.clientY - oy) / zoom });
        return next;
      });
    } else if (panning.current) {
      const { ox, oy, px, py } = panning.current;
      setPan({ x: px + (e.clientX - ox), y: py + (e.clientY - oy) });
    }
  }, [zoom]);

  const onMouseUp = useCallback(() => {
    dragging.current = null;
    panning.current = null;
  }, []);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.max(0.3, Math.min(2.5, z * (e.deltaY < 0 ? 1.1 : 0.9))));
  }, []);

  if (data.nodes.length === 0) return null;

  const getColor = (type: string) => NODE_COLORS[type] || { fill: '#f9fafb', stroke: '#9ca3af', text: '#374151' };

  return (
    <div className="relative select-none" style={{ height }}>
      <svg
        ref={svgRef}
        width={dims.w}
        height={dims.h}
        className="cursor-grab active:cursor-grabbing"
        onMouseDown={onSvgMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
      >
        <defs>
          {/* Arrow markers per edge type */}
          {Object.entries(EDGE_COLORS).map(([type, color]) => (
            <marker
              key={type}
              id={`arrow-${type}`}
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="3"
              orient="auto"
            >
              <path d="M0,0 L8,3 L0,6 Z" fill={color} opacity={0.7} />
            </marker>
          ))}
        </defs>

        <g transform={`translate(${pan.x},${pan.y}) scale(${zoom})`}>
          {/* ── Edges ── */}
          {data.edges.map((e, i) => {
            const a = pos.get(e.source), b = pos.get(e.target);
            if (!a || !b) return null;
            const color = EDGE_COLORS[e.type] || '#9ca3af';
            // Mid-point for edge label
            const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
            return (
              <g key={i}>
                <line
                  x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke={color}
                  strokeWidth={1.5}
                  opacity={0.55}
                  markerEnd={`url(#arrow-${e.type})`}
                />
                <text
                  x={mx} y={my - 4}
                  textAnchor="middle"
                  fontSize={8}
                  fill={color}
                  opacity={0.7}
                  pointerEvents="none"
                >
                  {e.type.replace(/_/g, ' ')}
                </text>
              </g>
            );
          })}

          {/* ── Nodes ── */}
          {data.nodes.map((n) => {
            const p = pos.get(n.id);
            if (!p) return null;
            const c = getColor(n.node_type);
            const isSelected = selected?.id === n.id;
            // Truncate label to ~18 chars
            const label = n.label.length > 18 ? n.label.slice(0, 16) + '…' : n.label;
            const typeShort = n.node_type.replace('JAVA_', 'J:').replace('XSLT_', 'X:');
            const rw = Math.max(label.length * 5.5 + 16, 70), rh = 32;

            return (
              <g
                key={n.id}
                transform={`translate(${p.x - rw / 2},${p.y - rh / 2})`}
                style={{ cursor: 'pointer' }}
                onMouseDown={(e) => onNodeMouseDown(e, n.id)}
                onClick={() => setSelected(isSelected ? null : n)}
              >
                <rect
                  width={rw} height={rh}
                  rx={6}
                  fill={c.fill}
                  stroke={isSelected ? '#dc2626' : c.stroke}
                  strokeWidth={isSelected ? 2 : 1}
                  filter={isSelected ? 'drop-shadow(0 2px 6px rgba(220,38,38,0.3))' : undefined}
                />
                <text
                  x={rw / 2} y={11}
                  textAnchor="middle"
                  fontSize={8}
                  fontWeight={700}
                  fill={c.stroke}
                  opacity={0.7}
                  letterSpacing={0.5}
                >
                  {typeShort}
                </text>
                <text
                  x={rw / 2} y={24}
                  textAnchor="middle"
                  fontSize={9.5}
                  fontWeight={600}
                  fill={c.text}
                >
                  {label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Controls */}
      <div className="absolute top-2 right-2 flex flex-col gap-1">
        <button
          onClick={() => setZoom((z) => Math.min(2.5, z * 1.2))}
          className="w-7 h-7 flex items-center justify-center rounded bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm font-bold shadow-sm"
        >+</button>
        <button
          onClick={() => setZoom((z) => Math.max(0.3, z * 0.8))}
          className="w-7 h-7 flex items-center justify-center rounded bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm font-bold shadow-sm"
        >−</button>
        <button
          onClick={() => { setPan({ x: 0, y: 0 }); setZoom(1); }}
          className="w-7 h-7 flex items-center justify-center rounded bg-white border border-gray-200 text-gray-500 hover:bg-gray-50 shadow-sm"
          title="Reset view"
        >
          <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" />
          </svg>
        </button>
      </div>

      {/* Selected node detail */}
      {selected && (
        <div className="absolute bottom-2 left-2 right-2 bg-white rounded-lg border border-gray-200 shadow-lg p-3 text-[11px]">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div
                className="font-bold text-[12px] mb-0.5 truncate"
                style={{ color: getColor(selected.node_type).text }}
              >
                {selected.label}
              </div>
              <div className="text-gray-400 mb-1.5">{selected.node_type}</div>
              {selected.file_path && (
                <div className="font-mono text-[10px] text-gray-500 truncate">
                  {selected.file_path.split('/').slice(-2).join('/')}{selected.line_number ? `:${selected.line_number}` : ''}
                </div>
              )}
              {selected.code_snippet && (
                <pre className="mt-1.5 text-[9.5px] bg-gray-50 rounded p-1.5 overflow-x-auto font-mono text-gray-600 max-h-[60px] whitespace-pre-wrap">
                  {selected.code_snippet.slice(0, 200)}
                </pre>
              )}
            </div>
            <button
              onClick={() => setSelected(null)}
              className="shrink-0 text-gray-400 hover:text-gray-600"
            >
              <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
