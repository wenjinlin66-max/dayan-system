import { http } from './client'

export const fetchWorkflowHealth = async () => http.get('/v1/workflows/health')
