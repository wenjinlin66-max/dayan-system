import { defineStore } from 'pinia'

import type { ApprovalTask, ChatMessage, ChatSession, WorkflowCatalogItem } from '@/types/chat'
import type { ExecutionStatus } from '@/types/execution'

export const useChatStore = defineStore('chat', {
  state: () => ({
    currentSessionId: '' as string,
    currentDeptId: '' as string,
    sessions: [] as ChatSession[],
    messages: [] as ChatMessage[],
    catalog: [] as WorkflowCatalogItem[],
    latestExecution: null as ExecutionStatus | null,
    sending: false,
    streamConnected: false,
    streamFallback: false,
    startingWorkflowId: '' as string,
    approvalTasks: [] as ApprovalTask[],
    selectedApprovalTaskId: '' as string,
    approvalSubmitting: false,
  }),
  actions: {
    setSessions(items: ChatSession[]) {
      this.sessions = items
      if (!this.currentDeptId && items.length > 0) {
        this.currentDeptId = items[0].dept_id
      }
    },
    setCurrentSession(sessionId: string) {
      this.currentSessionId = sessionId
      const matched = this.sessions.find((item) => item.session_id === sessionId)
      if (matched) {
        this.currentDeptId = matched.dept_id
      }
    },
    setCurrentDept(deptId: string) {
      this.currentDeptId = deptId
    },
    setMessages(items: ChatMessage[]) {
      this.messages = items
    },
    pushMessage(item: ChatMessage) {
      this.messages.push(item)
    },
    setCatalog(items: WorkflowCatalogItem[]) {
      this.catalog = items
    },
    setLatestExecution(item: ExecutionStatus | null) {
      this.latestExecution = item
    },
    setStreamConnected(value: boolean) {
      this.streamConnected = value
    },
    setStreamFallback(value: boolean) {
      this.streamFallback = value
    },
    setStartingWorkflowId(workflowId: string) {
      this.startingWorkflowId = workflowId
    },
    setApprovalTasks(items: ApprovalTask[]) {
      this.approvalTasks = items
      if (!this.selectedApprovalTaskId && items.length > 0) {
        this.selectedApprovalTaskId = items[0].approval_task_id
      }
      if (items.length === 0) {
        this.selectedApprovalTaskId = ''
      }
    },
    setSelectedApprovalTask(approvalTaskId: string) {
      this.selectedApprovalTaskId = approvalTaskId
    },
    setApprovalSubmitting(value: boolean) {
      this.approvalSubmitting = value
    },
  },
})
