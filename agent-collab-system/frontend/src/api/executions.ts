import { http } from './client'

export const fetchExecution = async (executionId: string) => http.get(`/v1/executions/${executionId}`)

export interface MockEventInjectPayload {
  workflow_id: string
  version?: number
  mode?: 'draft' | 'released'
  dept_id?: string
  event_type: string
  source: string
  event: Record<string, unknown>
  input_values?: Record<string, unknown>
  knowledge_docs?: Array<Record<string, unknown>>
}

export const injectMockEvent = async (payload: MockEventInjectPayload) => http.post('/v1/executions/inject/mock-event', payload)
