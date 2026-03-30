import client from './client';
import type { TraceResult, TraceRequest, TraceConfig } from '../types';

export const traceApi = {
  traceField: (req: TraceRequest): Promise<TraceResult> =>
    client.post<TraceResult>('/trace/field', req).then((r) => r.data),

  getGraph: (fieldName: string) =>
    client.get(`/graph/field/${encodeURIComponent(fieldName)}`).then((r) => r.data),

  getPipelineGraph: (fieldName: string) =>
    client.get(`/graph/field/${encodeURIComponent(fieldName)}/pipeline`).then((r) => r.data),

  getBranchGraph: (fieldName: string) =>
    client.get(`/graph/field/${encodeURIComponent(fieldName)}/branches`).then((r) => r.data),

  getConfig: (): Promise<{ trace: TraceConfig }> =>
    client.get('/config/').then((r) => r.data),

  updateConfig: (config: Partial<TraceConfig>) =>
    client.put('/config/', { trace: config }).then((r) => r.data),

  getLogs: (traceId: string) =>
    client.get(`/logs/${encodeURIComponent(traceId)}`).then((r) => r.data),

  getRecentLogs: () =>
    client.get('/logs/').then((r) => r.data),
};
