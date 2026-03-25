import { useQuery } from '@tanstack/react-query';
import { getBusinessDescription } from '../api/llm';

export function useBusinessDescription(
  fieldName: string,
  jurisdictionId: string,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ['businessDescription', fieldName, jurisdictionId],
    queryFn: () => getBusinessDescription(fieldName, jurisdictionId),
    enabled: enabled && !!fieldName && !!jurisdictionId,
  });
}
