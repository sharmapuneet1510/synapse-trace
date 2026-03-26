export interface TraceNode {
  id: string;
  label: string;
  node_type: string;
  file_path?: string;
  line_number?: number;
  code_snippet?: string;
  properties: Record<string, unknown>;
}

export interface TraceEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface TraceResponse {
  variable_name: string;
  jurisdiction_id: string;
  variations_searched: string[];
  nodes: TraceNode[];
  edges: TraceEdge[];
  node_count: number;
  edge_count: number;
  parse_status: string;
}
