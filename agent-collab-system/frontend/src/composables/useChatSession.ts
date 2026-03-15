import { ElMessage } from 'element-plus'

import { useApprovals } from '@/composables/useApprovals'
import { createChatSession, deleteChatSession, fetchChatMessages, fetchChatSessions, fetchWorkflowCatalog, sendChatMessage, startWorkflowFromChat } from '@/api/chat'
import { fetchExecution } from '@/api/executions'
import { useChatStore } from '@/store/chat'
import { useExecutionStream } from '@/composables/useExecutionStream'

export const useChatSession = () => {
  const chatStore = useChatStore()
  const executionStream = useExecutionStream()
  const approvals = useApprovals()

  const initialize = async () => {
    const sessionsRes = await refreshSessions()

    let sessionId = chatStore.currentSessionId
    if (!sessionId) {
      if (sessionsRes.length > 0) {
        sessionId = sessionsRes[0].session_id
      } else {
        const created = await createChatSession('当前部门主对话框')
        sessionId = created.data.session_id
        chatStore.setSessions([created.data])
        chatStore.setCurrentDept(created.data.dept_id)
      }
      chatStore.setCurrentSession(sessionId)
    }

    await Promise.all([loadMessages(sessionId), loadCatalog(), approvals.loadApprovalTasks()])
  }

  const selectSession = async (sessionId: string) => {
    chatStore.setCurrentSession(sessionId)
    await Promise.all([loadMessages(sessionId), loadCatalog(), approvals.loadApprovalTasks()])
  }

  const createSession = async (title = '新的部门对话会话') => {
    const created = await createChatSession(title)
    chatStore.setSessions([created.data, ...chatStore.sessions])
    await selectSession(created.data.session_id)
  }

  const refreshSessions = async () => {
    const sessionsRes = await fetchChatSessions()
    chatStore.setSessions(sessionsRes.data)
    if (sessionsRes.data.length > 0 && !chatStore.currentDeptId) {
      chatStore.setCurrentDept(sessionsRes.data[0].dept_id)
    }
    return sessionsRes.data
  }

  const deleteSession = async (sessionId: string) => {
    await deleteChatSession(sessionId)
    const deletingCurrent = chatStore.currentSessionId === sessionId
    chatStore.removeSession(sessionId)

    if (chatStore.sessions.length === 0) {
      await createSession('新的部门对话会话')
      return
    }

    if (deletingCurrent && chatStore.currentSessionId) {
      await selectSession(chatStore.currentSessionId)
      return
    }

    await Promise.all([loadCatalog(), approvals.loadApprovalTasks()])
  }

  const loadMessages = async (sessionId: string) => {
    const res = await fetchChatMessages(sessionId)
    chatStore.setMessages(res.data.items)
  }

  const loadCatalog = async () => {
    const res = await fetchWorkflowCatalog()
    chatStore.setCatalog(res.data.items)
  }

  const sendMessage = async (content: string) => {
    if (!chatStore.currentSessionId || !content.trim()) {
      return
    }
    try {
      chatStore.sending = true
      const userMessage = {
        message_id: `local_${Date.now()}`,
        session_id: chatStore.currentSessionId,
        role: 'user' as const,
        content,
        payload: null,
      }
      chatStore.pushMessage(userMessage)

      const res = await sendChatMessage(chatStore.currentSessionId, content)
      chatStore.pushMessage(res.data)

      if (res.data.related_execution_id) {
        const executionRes = await fetchExecution(res.data.related_execution_id)
        chatStore.setLatestExecution(executionRes.data)
        executionStream.start(res.data.related_execution_id)
      }
      await Promise.all([loadMessages(chatStore.currentSessionId), loadCatalog(), approvals.loadApprovalTasks(), refreshSessions()])
    } catch (error) {
      ElMessage.error(`发送消息失败：${String(error)}`)
    } finally {
      chatStore.sending = false
    }
  }

  return {
    ready: true,
    initialize,
    selectSession,
    createSession,
    deleteSession,
    sendMessage,
    loadMessages,
    loadCatalog,
    startSelectedWorkflow: async (
      workflowId: string,
      source = 'catalog',
      sourceMessageId?: string,
      inputValues?: Record<string, unknown>,
      note?: string,
    ) => {
      if (!chatStore.currentSessionId) {
        return
      }
      try {
        chatStore.setStartingWorkflowId(workflowId)
        const res = await startWorkflowFromChat(chatStore.currentSessionId, workflowId, {
          source,
          note,
          source_message_id: sourceMessageId,
          input_values: inputValues,
        })
        chatStore.pushMessage(res.data)
        if (res.data.related_execution_id) {
          const executionRes = await fetchExecution(res.data.related_execution_id)
          chatStore.setLatestExecution(executionRes.data)
          executionStream.start(res.data.related_execution_id)
        }
        await Promise.all([loadMessages(chatStore.currentSessionId), approvals.loadApprovalTasks(), refreshSessions()])
      } catch (error) {
        ElMessage.error(`启动 workflow 失败：${String(error)}`)
      } finally {
        chatStore.setStartingWorkflowId('')
      }
    },
  }
}
