import { useQuery } from '@tanstack/react-query';
import { fetchFieldDetail } from '../api/fields';

export function useFieldDetail(jurisdictionId: string | null, fieldName: string | null) {
  return useQuery({
    queryKey: ['fieldDetail', jurisdictionId, fieldName],
    queryFn: () => fetchFieldDetail(jurisdictionId!, fieldName!),
    enabled: !!jurisdictionId && !!fieldName,
  });
}
