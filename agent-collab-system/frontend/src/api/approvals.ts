import { http } from './client'

export const fetchApprovalTasks = async (params?: { dept_id?: string; include_all?: boolean }) => http.get('/v1/approvals', { params })

export const resumeApprovalTask = async (payload: {
  execution_id: string
  go_approval_id: string
  decision: string
  comment?: string
}) => http.post('/v1/approvals/resume', payload)
