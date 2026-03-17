import { http } from './client'

export const createChatSession = async (title?: string) => http.post('/v1/chat/sessions', { title })

export const fetchChatSessions = async (params?: { dept_id?: string; include_all?: boolean }) => http.get('/v1/chat/sessions', { params })

export const deleteChatSession = async (sessionId: string, params?: { dept_id?: string; include_all?: boolean }) => http.delete(`/v1/chat/sessions/${sessionId}`, { params })

export const sendChatMessage = async (sessionId: string, content: string, params?: { dept_id?: string; include_all?: boolean }) =>
  http.post(`/v1/chat/sessions/${sessionId}/messages`, { content, message_type: 'text' }, { params })

export const fetchChatMessages = async (sessionId: string, params?: { dept_id?: string; include_all?: boolean }) => http.get(`/v1/chat/sessions/${sessionId}/messages`, { params })

export const fetchWorkflowCatalog = async (params?: { category?: string; dept_id?: string; include_all?: boolean }) =>
  http.get('/v1/chat/workflows/catalog', { params })

export const routeChatMessage = async (payload: { session_id?: string; content: string }) =>
  http.post('/v1/chat/route', payload)

export const startWorkflowFromChat = async (
  sessionId: string,
  workflowId: string,
  payload?: { source?: string; note?: string; source_message_id?: string; input_values?: Record<string, unknown> },
  params?: { dept_id?: string; include_all?: boolean },
) =>
  http.post(`/v1/chat/sessions/${sessionId}/workflows/${workflowId}/start`, payload ?? { source: 'catalog' }, { params })
