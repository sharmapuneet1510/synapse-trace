export interface TraceConfig {
  includePackages: string[];
  excludePackages: string[];
  stopPackages: string[];
  maxDepth: number;
  followInternalCallsOnly: boolean;
  enableConditionTracing: boolean;
  enableXsltImports: boolean;
}

export interface TraceRequest {
  field_name: string;
  jurisdiction?: string;
  package_filters?: string[];
  max_depth?: number;
  enable_condition_tracing?: boolean;
  enable_xslt_imports?: boolean;
}
