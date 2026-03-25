import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getSessions,
  getSession,
  sendMessage,
  createSession,
  deleteSession,
} from '../api/chat';

export function useChatSessions() {
  return useQuery({
    queryKey: ['chatSessions'],
    queryFn: getSessions,
    refetchOnWindowFocus: true,
  });
}

export function useChatSession(sessionId: string | null) {
  return useQuery({
    queryKey: ['chatSession', sessionId],
    queryFn: () => getSession(sessionId!),
    enabled: !!sessionId,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      content,
      jurisdictionId,
      fieldName,
    }: {
      sessionId: string;
      content: string;
      jurisdictionId?: string;
      fieldName?: string;
    }) => sendMessage(sessionId, content, jurisdictionId, fieldName),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['chatSession', variables.sessionId],
      });
    },
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (title?: string) => createSession(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
    },
  });
}

export function useDeleteSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteSession(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
    },
  });
}
