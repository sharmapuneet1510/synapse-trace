import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats, fetchParseLogs, fetchNodes, fetchEdges } from '../api/dashboard';

export function useDashboardStats(refetchInterval = 3000) {
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: fetchDashboardStats,
    refetchInterval,
  });
}

export function useParseLogs(limit = 100, refetchInterval = 2000) {
  return useQuery({
    queryKey: ['parseLogs', limit],
    queryFn: () => fetchParseLogs(limit),
    refetchInterval,
  });
}

export function useNodes(jurisdictionId: string | null, limit = 100, offset = 0) {
  return useQuery({
    queryKey: ['nodes', jurisdictionId, limit, offset],
    queryFn: () => fetchNodes(jurisdictionId!, limit, offset),
    enabled: !!jurisdictionId,
  });
}

export function useEdges(jurisdictionId: string | null, limit = 100, offset = 0) {
  return useQuery({
    queryKey: ['edges', jurisdictionId, limit, offset],
    queryFn: () => fetchEdges(jurisdictionId!, limit, offset),
    enabled: !!jurisdictionId,
  });
}
