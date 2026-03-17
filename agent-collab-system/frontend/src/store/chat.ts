import { defineStore } from 'pinia'

import type { ApprovalTask, ChatMessage, ChatSession, WorkflowCatalogItem } from '@/types/chat'
import type { ExecutionStatus } from '@/types/execution'
import { getChatIdentityProfile, loadStoredChatIdentityContext, saveStoredChatIdentityContext, type ChatScopeMode } from '@/utils/chatIdentity'

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
    activeProfileId: loadStoredChatIdentityContext().profileId,
    scopeMode: loadStoredChatIdentityContext().scopeMode as ChatScopeMode,
    scopeDeptId: loadStoredChatIdentityContext().scopeDeptId,
    approvalFilterDeptId: '' as string,
    executionFilterDeptId: '' as string,
    latestExecutionByDept: {} as Record<string, ExecutionStatus>,
  }),
  getters: {
    activeProfile: (state) => getChatIdentityProfile(state.activeProfileId),
  },
  actions: {
    setSessions(items: ChatSession[]) {
      this.sessions = items
      if (!this.currentDeptId && items.length > 0) {
        this.currentDeptId = items[0].dept_id
      }
    },
    removeSession(sessionId: string) {
      this.sessions = this.sessions.filter((item) => item.session_id !== sessionId)
      if (this.currentSessionId === sessionId) {
        this.currentSessionId = this.sessions[0]?.session_id ?? ''
        this.currentDeptId = this.sessions[0]?.dept_id ?? this.currentDeptId
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
      if (item?.dept_id) {
        this.latestExecutionByDept[item.dept_id] = item
      }
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
    setApprovalFilterDeptId(value: string) {
      this.approvalFilterDeptId = value
    },
    setExecutionFilterDeptId(value: string) {
      this.executionFilterDeptId = value
    },
    persistIdentityContext() {
      saveStoredChatIdentityContext({
        profileId: this.activeProfileId,
        scopeMode: this.scopeMode,
        scopeDeptId: this.scopeDeptId,
      })
    },
    applyIdentityProfile(profileId: string) {
      this.activeProfileId = profileId
      const profile = getChatIdentityProfile(profileId)
      this.scopeMode = profile.roles.includes('ceo') ? this.scopeMode : 'department'
      this.scopeDeptId = profile.roles.includes('ceo') ? (this.scopeDeptId || 'production') : profile.deptId
      this.currentSessionId = ''
      this.messages = []
      this.sessions = []
      this.catalog = []
      this.approvalTasks = []
      this.approvalFilterDeptId = ''
      this.executionFilterDeptId = ''
      this.latestExecutionByDept = {}
      this.persistIdentityContext()
    },
    applyScopeMode(scopeMode: ChatScopeMode) {
      this.scopeMode = scopeMode
      if (!this.scopeDeptId) {
        this.scopeDeptId = 'production'
      }
      if (scopeMode === 'all_departments') {
        this.currentSessionId = ''
      }
      this.persistIdentityContext()
    },
    applyScopeDeptId(deptId: string) {
      this.scopeDeptId = deptId
      if (deptId) {
        this.currentDeptId = deptId
      }
      this.approvalFilterDeptId = deptId
      this.executionFilterDeptId = deptId
      this.persistIdentityContext()
    },
    syncIdentityFromAuth(payload: { userId: string; deptId: string; roles: string[]; profileId: string }) {
      this.activeProfileId = payload.profileId
      this.scopeMode = payload.roles.includes('ceo') ? 'all_departments' : 'department'
      this.scopeDeptId = payload.roles.includes('ceo') ? (this.scopeDeptId || 'production') : payload.deptId
      this.currentDeptId = payload.roles.includes('ceo') ? (this.scopeDeptId || 'production') : payload.deptId
      this.currentSessionId = ''
      this.sessions = []
      this.messages = []
      this.catalog = []
      this.approvalTasks = []
      this.latestExecution = null
      this.latestExecutionByDept = {}
      this.approvalFilterDeptId = this.currentDeptId
      this.executionFilterDeptId = this.currentDeptId
      this.persistIdentityContext()
    },
    getEffectiveDeptId() {
      if (this.activeProfile.roles.includes('ceo')) {
        return this.scopeDeptId || this.currentDeptId || 'production'
      }
      return this.activeProfile.deptId
    },
    canViewAllDepartments() {
      return this.activeProfile.roles.includes('ceo')
    },
  },
})
