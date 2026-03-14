import type { WorkflowEdge, WorkflowNode } from '@/types/workflow'

export const compileDslPreview = (nodes: WorkflowNode[], edges: WorkflowEdge[]) => {
  const incoming = new Set(edges.map((edge) => edge.target))
  const entrypoint = nodes.find((node) => !incoming.has(node.id))?.id ?? nodes[0]?.id ?? null

  return {
    entrypoint,
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.type,
      name: node.label,
      config: node.config,
      runtime: {},
    })),
    edges: edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      label: edge.label,
    })),
  }
}
