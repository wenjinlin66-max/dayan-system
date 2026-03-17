import { http } from './client'

export const login = async (payload: { username: string; password: string }) => http.post('/v1/auth/login', payload)

export const fetchCurrentIdentity = async () => http.get('/v1/auth/me')
