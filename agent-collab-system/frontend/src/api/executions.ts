import { http } from './client'
import type { WorkflowExecutionHistoryResponse } from '@/types/execution'

export const fetchExecution = async (executionId: string, params?: { dept_id?: string; include_all?: boolean }) => http.get(`/v1/executions/${executionId}`, { params })

export const fetchWorkflowExecutionHistory = async (workflowId: string, params?: { include_all?: boolean }) =>
  http.get<WorkflowExecutionHistoryResponse>(`/v1/executions/workflow/${workflowId}/history`, { params })

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
