export type TransformationType =
  | 'EXTRACTION' | 'MAPPING' | 'ENRICHMENT' | 'OVERRIDE'
  | 'DEFAULTING' | 'PASS_THROUGH' | 'CONDITIONAL_ASSIGNMENT' | 'FINAL_REPORT_ASSIGNMENT';

export type OriginType = 'XSLT' | 'JAVA' | 'XSLT_THEN_JAVA' | 'UNKNOWN';

export interface Evidence {
  repository?: string;
  module?: string;
  package?: string;
  class_or_template?: string;
  method_or_template_name?: string;
  file_path?: string;
  line_number?: number;
  line_range?: [number, number];
  transformation_type?: TransformationType;
  condition_text?: string;
  raw_code?: string;
}

export interface TraceNodeData {
  node_id: string;
  label: string;
  node_type: 'java_method' | 'xslt_template' | 'field' | 'condition' | 'origin';
  transformation_type?: TransformationType;
  evidence: Evidence;
  metadata: Record<string, unknown>;
}

export interface TraceEdge {
  source_id: string;
  target_id: string;
  relation: string;
  condition_text?: string;
  label?: string;
}

export interface BranchPath {
  branch_id: string;
  condition: string;
  nodes: TraceNodeData[];
  edges: TraceEdge[];
  outcome?: string;
}

export interface TraceSummary {
  field_name: string;
  origin: OriginType;
  pipeline_steps: string[];
  branch_count: number;
  total_nodes: number;
  has_xslt: boolean;
  has_java: boolean;
  technical_explanation: string;
  business_explanation: string;
}

export interface PipelineStep {
  step_id: string;
  order: number;
  label: string;
  type: string;
  transformation_type?: TransformationType;
  evidence?: Evidence;
}

export interface GraphJSON {
  nodes: Array<{ id: string; label: string; type: string; properties: Record<string, unknown> }>;
  edges: Array<{ source: string; target: string; relation: string; properties: Record<string, unknown> }>;
  metadata: Record<string, unknown>;
}

export interface TraceResult {
  trace_id: string;
  field_name: string;
  origin: OriginType;
  summary: TraceSummary;
  pipeline: PipelineStep[];
  branches: BranchPath[];
  evidence: Evidence[];
  technical_explanation: string;
  business_explanation: string;
  graph_json: GraphJSON;
  metadata: Record<string, unknown>;
}
