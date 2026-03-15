export interface WorkflowSummary {
  workflow_id: string
  code: string
  name: string
  mode: string
  owner_dept_id: string
  workflow_category: string
  workflow_trigger_type: string
  latest_draft_version?: number | null
  current_release_version?: number | null
}

export interface WorkflowNode {
  id: string
  type: string
  label: string
  config: Record<string, unknown>
  position?: {
    x: number
    y: number
  }
}

export interface WorkflowEdge {
  id: string
  source: string
  target: string
  label?: string
}

export interface WorkflowUiSchema {
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  viewport?: Record<string, unknown>
}

export interface WorkflowCompileResult {
  workflow_id: string
  version: number
  mode: string
  compile_status: string
  ui_schema: WorkflowUiSchema
  execution_dag: Record<string, unknown> | null
  compile_errors: Array<Record<string, unknown>> | null
  release_note?: string | null
  is_current_release: boolean
}

export interface WorkflowVersionListResponse {
  workflow_id: string
  versions: WorkflowCompileResult[]
}

export type WorkflowNodeType =
  | 'dialog_agent'
  | 'sensor_agent'
  | 'decision_agent'
  | 'execution_agent'
  | 'condition'
  | 'approval'
  | 'wait'
  | 'exception'

export type ExecutionTargetType = 'go_api' | 'department_table'

export interface DepartmentTableTargetConfig {
  target_type: 'department_table'
  target_ref: string
  provider: string
  operation: 'append_row' | 'upsert_row' | 'update_row'
  dept_route_mode: 'current_dept' | 'fixed_dept' | 'derived'
  fixed_dept_id?: string
  idempotency_key_template?: string
  row_mapping?: Record<string, string>
  default_values?: Record<string, string>
}

export interface ExecutionNodeConfig {
  description?: string
  execution_target_mode?: 'manual' | 'ai_select'
  execution_targets?: DepartmentTableTargetConfig[]
  approval_mode?: 'always' | 'risk_based' | 'never'
  approval_required?: boolean
  result_delivery?: 'chat' | 'event' | 'monitor'
  result_target_dept_id?: string
}

export interface SensorConditionConfig {
  field: string
  operator: 'eq' | 'ne' | '>' | '>=' | '<' | '<='
  value?: string | number | boolean
  value_from_field?: string
}

export interface SensorSourceTypeOption {
  value: SensorNodeConfig['source_type']
  label: string
}

export interface SensorOperatorOption {
  value: SensorConditionConfig['operator']
  label: string
  supported_field_types: string[]
}

export interface SensorFieldOption {
  value: string
  label: string
  field_type: 'string' | 'number' | 'boolean'
  suggested_values: string[]
}

export interface SensorEventKeyOption {
  value: string
  label: string
}

export interface SensorTableOption {
  value: string
  label: string
  event_keys: SensorEventKeyOption[]
  fields: SensorFieldOption[]
}

export interface SensorSourceOption {
  value: string
  label: string
  source_type: NonNullable<SensorNodeConfig['source_type']>
  tables: SensorTableOption[]
}

export interface SensorMetadataResponse {
  source_types: SensorSourceTypeOption[]
  operators: SensorOperatorOption[]
  sources: SensorSourceOption[]
}

export interface SensorNodeConfig {
  description?: string
  source_type?: 'iot' | 'form_change' | 'supply_chain_event' | 'third_party_notice' | 'schedule' | 'manual'
  source_system?: string
  source_table?: string
  source_event_key?: string
  selected_fields?: string[]
  condition_logic?: 'and' | 'or'
  conditions?: SensorConditionConfig[]
  output_event_name?: string
  output_mapping?: Record<string, string>
  pass_raw_payload?: boolean
}

export interface DecisionNodeConfig {
  description?: string
  decision_mode?: 'rule' | 'model' | 'llm'
  rule_set_ref?: string
  rule_config?: Record<string, unknown>
  model_type?: 'scorecard' | 'capacity_planner' | 'risk_balancer'
  model_ref?: string
  model_params?: Record<string, unknown>
  optimization_goal?: string
  constraints?: string[]
  prompt_template?: string
  output_template?: string
  include_explanation?: boolean
  include_citations?: boolean
  rag_refs?: string[]
}

export interface DialogNodeConfig {
  description?: string
  promptHint?: string
  intentTag?: string
  responseStyle?: 'guide' | 'confirm' | 'explain'
  memoryProfile?: 'light' | 'standard' | 'deep'
}

export interface ConditionNodeConfig {
  description?: string
  expression?: string
  trueLabel?: string
  falseLabel?: string
}

export interface ApprovalNodeConfig {
  description?: string
  approvalPolicy?: string
  approvalTitle?: string
  approverScope?: string
  timeoutAction?: string
}

export interface WaitNodeConfig {
  description?: string
  waitMode?: string
  waitValue?: string
  resumeEvent?: string
}

export interface ExceptionNodeConfig {
  description?: string
  exceptionPolicy?: string
  fallbackNode?: string
  notifyTarget?: string
}
