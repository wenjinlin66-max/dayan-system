export interface ChatSession {
  session_id: string
  title: string
  dept_id: string
  last_message_at?: string | null
}

export type ChatRouteType = 'ask' | 'approve' | 'command'

export interface WorkflowCatalogItem {
  workflow_id: string
  title: string
  category: string
  summary: string
  dept_id: string
  confidence?: number | null
  required_inputs?: string[]
  input_schema?: Record<string, unknown> | null
}

export interface ChatMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string | null
  route_type?: ChatRouteType | null
  related_execution_id?: string | null
  payload?: Record<string, unknown> | null
}

export interface ChatRouteResponse {
  route_type: ChatRouteType
  needs_confirmation: boolean
  candidate_workflows: WorkflowCatalogItem[]
  missing_inputs: string[]
  execution_id?: string | null
  reply?: string | null
}

export interface ApprovalTask {
  approval_task_id: string
  go_approval_id: string
  execution_id: string
  workflow_id: string
  dept_id: string
  current_node?: string | null
  title: string
  summary: string
  status: string
  decision?: string | null
  comment?: string | null
}
