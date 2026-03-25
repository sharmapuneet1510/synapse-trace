export interface DashboardStats {
  batch_status: string;
  batch_started: string | null;
  batch_completed: string | null;
  totals: {
    java_findings: number;
    xslt_findings: number;
    nodes: number;
    edges: number;
  };
  jurisdictions: JurisdictionStatus[];
}

export interface JurisdictionStatus {
  id: string;
  status: string;
  java_findings: number;
  xslt_findings: number;
  nodes: number;
  edges: number;
  parsed_at: string | null;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  jurisdiction_id: string | null;
}
