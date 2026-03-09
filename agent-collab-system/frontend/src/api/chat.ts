import { http } from './client'

export const createChatSession = async (title?: string) => http.post('/v1/chat/sessions', { title })
