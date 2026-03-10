export interface ChatSession {
  sessionId: string
  title: string
}

export type ChatRouteType = 'ask' | 'approve' | 'command'

export interface WorkflowCatalogItem {
  workflowId: string
  title: string
  category: string
  confidence?: number
}
