import { http } from './client'
import type { SensorMetadataResponse, WorkflowDialogTriggerConfig, WorkflowUiSchema } from '@/types/workflow'

export const fetchWorkflowHealth = async () => http.get('/v1/workflows/health')
export const fetchWorkflows = async (params?: { dept_id?: string; include_all?: boolean }) => http.get('/v1/workflows', { params })
export const fetchSensorMetadata = async () => http.get<SensorMetadataResponse>('/v1/workflows/sensor-metadata')
export const deleteWorkflow = async (workflowId: string, params?: { dept_id?: string }) => http.delete(`/v1/workflows/${workflowId}`, { params })

export const createWorkflow = async (payload: { name: string; code: string; visibility?: string; ui_schema: WorkflowUiSchema; owner_dept_id?: string }) =>
  http.post('/v1/workflows', payload)

export const saveWorkflowDraft = async (
  workflowId: string,
  payload: { name?: string; ui_schema: WorkflowUiSchema; schema_version?: string },
  params?: { dept_id?: string },
) => http.put(`/v1/workflows/${workflowId}/draft`, payload, { params })

export const compileWorkflow = async (workflowId: string, payload: { schema_version?: string; dept_id?: string } = {}) =>
  http.post(`/v1/workflows/${workflowId}/compile`, { schema_version: payload.schema_version }, { params: { dept_id: payload.dept_id } })

export const publishWorkflow = async (
  workflowId: string,
  payload: { release_note?: string; category?: string; summary?: string; dept_id?: string; dialog_trigger_config?: WorkflowDialogTriggerConfig },
) => http.post(
  `/v1/workflows/${workflowId}/publish`,
  {
    release_note: payload.release_note,
    category: payload.category,
    summary: payload.summary,
    dialog_trigger_config: payload.dialog_trigger_config,
  },
  { params: { dept_id: payload.dept_id } },
)

export const fetchWorkflowVersions = async (workflowId: string, params?: { dept_id?: string }) => http.get(`/v1/workflows/${workflowId}/versions`, { params })

export const fetchCurrentRelease = async (workflowId: string, params?: { dept_id?: string }) => http.get(`/v1/workflows/${workflowId}/releases/current`, { params })

export const fetchLatestDraft = async (workflowId: string, params?: { dept_id?: string }) => http.get(`/v1/workflows/${workflowId}/draft`, { params })
