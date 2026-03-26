import { useMutation } from '@tanstack/react-query';
import { traceVariable, type TraceRequest } from '../api/trace';

export function useTraceVariable() {
  return useMutation({
    mutationFn: (req: TraceRequest) => traceVariable(req),
  });
}
