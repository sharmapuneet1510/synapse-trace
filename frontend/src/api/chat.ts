import { api } from './client';
import type { ChatMessage, ChatSession, ChatSessionDetail } from '../types/chat';

export const createSession = (title?: string) =>
  api.post<ChatSession>('/chat/sessions', { title });

export const getSessions = () =>
  api.get<ChatSession[]>('/chat/sessions');

export const getSession = (id: string) =>
  api.get<ChatSessionDetail>(`/chat/sessions/${id}`);

export const sendMessage = (
  sessionId: string,
  content: string,
  jurisdictionId?: string,
  fieldName?: string,
) =>
  api.post<{ user_message: ChatMessage; assistant_message: ChatMessage }>(
    `/chat/sessions/${sessionId}/messages`,
    { content, jurisdiction_id: jurisdictionId, field_name: fieldName },
  );

export const deleteSession = (id: string) =>
  api.delete(`/chat/sessions/${id}`);
