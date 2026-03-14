import { fetchExecution } from '@/api/executions'
import { useChatStore } from '@/store/chat'
import type { ExecutionStatus } from '@/types/execution'

let currentSource: EventSource | null = null
let currentPollTimer: number | null = null

export const useExecutionStream = () => {
  const chatStore = useChatStore()

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

  const startPolling = (executionId: string) => {
    chatStore.setStreamFallback(true)
    currentPollTimer = window.setInterval(async () => {
      const response = await fetchExecution(executionId)
      const payload = response.data as ExecutionStatus
      chatStore.setLatestExecution(payload)
      if (payload.status === 'finished' || payload.status === 'failed' || payload.status === 'cancelled') {
        stop()
      }
    }, 2000)
  }

  const start = (executionId: string) => {
    stop()
    const source = new EventSource(`/api/v1/executions/${executionId}/stream`)
    currentSource = source
    chatStore.setStreamConnected(true)

    source.addEventListener('status', (event) => {
      const payload = JSON.parse((event as MessageEvent).data) as ExecutionStatus
      chatStore.setLatestExecution(payload)
      if (payload.status === 'finished' || payload.status === 'failed' || payload.status === 'cancelled') {
        stop()
      }
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
