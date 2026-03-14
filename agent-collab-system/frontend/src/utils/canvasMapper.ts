import type { WorkflowEdge, WorkflowNode, WorkflowUiSchema } from '@/types/workflow'

export const mapCanvasToDsl = (nodes: WorkflowNode[], edges: WorkflowEdge[]): WorkflowUiSchema => ({
  nodes: nodes.map((node) => ({
    ...node,
    label: node.label.trim() || node.type,
  })),
  edges,
  viewport: { x: 0, y: 0, zoom: 1 },
})
