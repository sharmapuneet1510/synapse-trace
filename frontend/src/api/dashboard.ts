import { api } from './client';
import type { DashboardStats, LogEntry } from '../types/dashboard';

export const fetchDashboardStats = () =>
  api.get<DashboardStats>('/dashboard/stats');

export const fetchParseLogs = (limit = 100) =>
  api.get<LogEntry[]>(`/parse/logs?limit=${limit}`);

export const triggerParse = () =>
  api.post<{ status: string; message: string }>('/parse/trigger', {});

export const fetchNodes = (jurisdictionId: string, limit = 100, offset = 0) =>
  api.get<{ nodes: Record<string, unknown>[]; total: number }>(
    `/dashboard/nodes/${jurisdictionId}?limit=${limit}&offset=${offset}`,
  );

export const fetchEdges = (jurisdictionId: string, limit = 100, offset = 0) =>
  api.get<{ edges: Record<string, unknown>[]; total: number }>(
    `/dashboard/edges/${jurisdictionId}?limit=${limit}&offset=${offset}`,
  );
