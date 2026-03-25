import { useQuery } from '@tanstack/react-query';
import { fetchJurisdictions, fetchConfigType } from '../api/jurisdictions';

export function useJurisdictions() {
  return useQuery({
    queryKey: ['jurisdictions'],
    queryFn: fetchJurisdictions,
  });
}

export function useConfigType(jurisdictionId: string | null, configType: string | null) {
  return useQuery({
    queryKey: ['configType', jurisdictionId, configType],
    queryFn: () => fetchConfigType(jurisdictionId!, configType!),
    enabled: !!jurisdictionId && !!configType,
  });
}
