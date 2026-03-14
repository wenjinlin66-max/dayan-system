export const WORKFLOW_TRIGGER_TYPE_OPTIONS = [
  { value: 'dialog_trigger', label: '对话触发' },
  { value: 'event_trigger', label: '事件触发' },
  { value: 'schedule_trigger', label: '定时触发' },
] as const

export type WorkflowCategoryValue = (typeof WORKFLOW_TRIGGER_TYPE_OPTIONS)[number]['value']

const WORKFLOW_TRIGGER_TYPE_LABELS = new Map<string, string>(WORKFLOW_TRIGGER_TYPE_OPTIONS.map((item) => [item.value, item.label]))

export const getWorkflowCategoryLabel = (value: string | null | undefined) =>
  WORKFLOW_TRIGGER_TYPE_LABELS.get(value ?? '') ?? value ?? '未分类'
