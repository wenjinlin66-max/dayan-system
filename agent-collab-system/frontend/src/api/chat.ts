import { http } from './client'

export const createChatSession = async (title?: string) => http.post('/v1/chat/sessions', { title })

export const fetchChatSessions = async () => http.get('/v1/chat/sessions')

export const deleteChatSession = async (sessionId: string) => http.delete(`/v1/chat/sessions/${sessionId}`)

export const sendChatMessage = async (sessionId: string, content: string) =>
  http.post(`/v1/chat/sessions/${sessionId}/messages`, { content, message_type: 'text' })

export const fetchChatMessages = async (sessionId: string) => http.get(`/v1/chat/sessions/${sessionId}/messages`)

export const fetchWorkflowCatalog = async (category?: string) =>
  http.get('/v1/chat/workflows/catalog', { params: category ? { category } : {} })

export const routeChatMessage = async (payload: { session_id?: string; content: string }) =>
  http.post('/v1/chat/route', payload)

export const startWorkflowFromChat = async (
  sessionId: string,
  workflowId: string,
  payload?: { source?: string; note?: string; source_message_id?: string; input_values?: Record<string, unknown> },
) =>
  http.post(`/v1/chat/sessions/${sessionId}/workflows/${workflowId}/start`, payload ?? { source: 'catalog' })
