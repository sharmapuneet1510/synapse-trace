import { api } from './client';
import type { TraceResponse } from '../types/trace';

export interface TraceRequest {
  variable_name: string;
  jurisdiction_id: string;
  additional_variations?: string[];
  max_depth?: number;
}

export function traceVariable(req: TraceRequest): Promise<TraceResponse> {
  return api.post<TraceResponse>('/trace/variable', req);
}
