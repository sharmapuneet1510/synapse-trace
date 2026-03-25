import { useQuery } from '@tanstack/react-query';
import { fetchTranslation } from '../api/translation';

export function useTranslation(
  fieldName: string | null,
  jurisdictionId: string | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ['translation', jurisdictionId, fieldName],
    queryFn: () => fetchTranslation(fieldName!, jurisdictionId!),
    enabled: enabled && !!fieldName && !!jurisdictionId,
  });
}
