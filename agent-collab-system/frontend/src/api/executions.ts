import { http } from './client'

export const fetchExecution = async (executionId: string) => http.get(`/v1/executions/${executionId}`)
