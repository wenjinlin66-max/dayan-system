import { http } from './client'
import type { SensorMetadataResponse, WorkflowUiSchema } from '@/types/workflow'

export const fetchWorkflowHealth = async () => http.get('/v1/workflows/health')
export const fetchWorkflows = async () => http.get('/v1/workflows')
export const fetchSensorMetadata = async () => http.get<SensorMetadataResponse>('/v1/workflows/sensor-metadata')
export const deleteWorkflow = async (workflowId: string) => http.delete(`/v1/workflows/${workflowId}`)

export const createWorkflow = async (payload: { name: string; code: string; visibility?: string; ui_schema: WorkflowUiSchema }) =>
  http.post('/v1/workflows', payload)

export const saveWorkflowDraft = async (
  workflowId: string,
  payload: { name?: string; ui_schema: WorkflowUiSchema; schema_version?: string },
) => http.put(`/v1/workflows/${workflowId}/draft`, payload)

export const compileWorkflow = async (workflowId: string, payload: { schema_version?: string } = {}) =>
  http.post(`/v1/workflows/${workflowId}/compile`, payload)

export const publishWorkflow = async (
  workflowId: string,
  payload: { release_note?: string; category?: string; summary?: string },
) => http.post(`/v1/workflows/${workflowId}/publish`, payload)

export const fetchWorkflowVersions = async (workflowId: string) => http.get(`/v1/workflows/${workflowId}/versions`)

export const fetchCurrentRelease = async (workflowId: string) => http.get(`/v1/workflows/${workflowId}/releases/current`)

export const fetchLatestDraft = async (workflowId: string) => http.get(`/v1/workflows/${workflowId}/draft`)
