import { http } from './client'

export const fetchApprovalTasks = async () => http.get('/v1/approvals')

export const resumeApprovalTask = async (payload: {
  execution_id: string
  go_approval_id: string
  decision: string
  comment?: string
}) => http.post('/v1/approvals/resume', payload)
