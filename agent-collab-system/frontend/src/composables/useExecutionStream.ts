import { fetchExecution } from '@/api/executions'
import { fetchApprovalTasks } from '@/api/approvals'
import { fetchChatMessages } from '@/api/chat'
import { useAuthStore } from '@/store/auth'
import { useChatStore } from '@/store/chat'
import type { ExecutionStatus } from '@/types/execution'

let currentSource: EventSource | null = null
let currentPollTimer: number | null = null

export const useExecutionStream = () => {
  const chatStore = useChatStore()
  const authStore = useAuthStore()

  const resolveExecutionParams = () => {
    if (chatStore.canViewAllDepartments()) {
      return {
        include_all: true,
        dept_id: chatStore.scopeDeptId || undefined,
      }
    }
    return {
      dept_id: chatStore.getEffectiveDeptId(),
    }
  }

  const stop = () => {
    currentSource?.close()
    currentSource = null
    if (currentPollTimer !== null) {
      window.clearInterval(currentPollTimer)
      currentPollTimer = null
    }
    chatStore.setStreamConnected(false)
    chatStore.setStreamFallback(false)
  }

  const refreshApprovalAndMessages = async () => {
    try {
      const params = resolveExecutionParams()
      const approvalRes = await fetchApprovalTasks(params)
      chatStore.setApprovalTasks(approvalRes.data.items)
      if (chatStore.currentSessionId) {
        const messagesRes = await fetchChatMessages(chatStore.currentSessionId, params)
        chatStore.setMessages(messagesRes.data.items)
      }
    } catch {
      // best effort refresh only
    }
  }

  const startPolling = (executionId: string) => {
    chatStore.setStreamFallback(true)
    currentPollTimer = window.setInterval(async () => {
      try {
        const response = await fetchExecution(executionId, resolveExecutionParams())
        const payload = response.data as ExecutionStatus
        chatStore.setLatestExecution(payload)
        if (payload.status === 'waiting_approval') {
          await refreshApprovalAndMessages()
        }
        if (payload.status === 'finished' || payload.status === 'failed' || payload.status === 'cancelled') {
          await refreshApprovalAndMessages()
          stop()
        }
      } catch {
        stop()
      }
    }, 2000)
  }

  const start = (executionId: string) => {
    stop()
    const params = resolveExecutionParams()
    const searchParams = new URLSearchParams()
    if (authStore.accessToken) {
      searchParams.set('access_token', authStore.accessToken)
    }
    if (params.include_all) {
      searchParams.set('include_all', 'true')
    }
    if (params.dept_id) {
      searchParams.set('dept_id', params.dept_id)
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : ''
    const source = new EventSource(`/api/v1/executions/${executionId}/stream${query}`)
    currentSource = source
    chatStore.setStreamConnected(true)

    source.addEventListener('status', (event) => {
      void (async () => {
        const payload = JSON.parse((event as MessageEvent).data) as ExecutionStatus
        chatStore.setLatestExecution(payload)
        if (payload.status === 'waiting_approval') {
          await refreshApprovalAndMessages()
        }
        if (payload.status === 'finished' || payload.status === 'failed' || payload.status === 'cancelled') {
          await refreshApprovalAndMessages()
          stop()
        }
      })()
    })

    source.onerror = () => {
      source.close()
      currentSource = null
      chatStore.setStreamConnected(false)
      if (!chatStore.streamFallback) {
        startPolling(executionId)
      }
    }
  }

  return {
    transport: 'sse-with-poll-fallback',
    start,
    stop,
  }
}
