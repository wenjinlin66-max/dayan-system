export interface ExecutionStatus {
  execution_id: string
  workflow_id: string
  workflow_version: number
  mode: string
  status: string
  current_node?: string | null
  thread_id: string
  dept_id: string
  started_at?: string | null
  updated_at?: string | null
  final_output?: Record<string, unknown> | null
}

export interface WorkflowExecutionHistoryItem {
  execution_id: string
  workflow_id: string
  workflow_name: string
  dept_id: string
  status: string
  execution_type: string
  task_summary: string
  target_summary: string
  started_at?: string | null
  updated_at?: string | null
}

export interface WorkflowExecutionHistoryResponse {
  workflow_id: string
  workflow_name: string
  items: WorkflowExecutionHistoryItem[]
}
