import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchApprovalTasks, resumeApprovalTask } from '@/api/approvals'
import { fetchChatMessages } from '@/api/chat'
import { fetchExecution } from '@/api/executions'
import { useExecutionStream } from '@/composables/useExecutionStream'
import { useChatStore } from '@/store/chat'

export const useApprovals = () => {
  const chatStore = useChatStore()
  const executionStream = useExecutionStream()
  const approvalComment = ref('')

  const approvalTasks = computed(() => chatStore.approvalTasks)
  const selectedApprovalTask = computed(() =>
    chatStore.approvalTasks.find((item) => item.approval_task_id === chatStore.selectedApprovalTaskId) ?? null,
  )

  const loadApprovalTasks = async () => {
    const params = chatStore.canViewAllDepartments()
      ? { include_all: true, dept_id: chatStore.scopeDeptId || undefined }
      : { dept_id: chatStore.getEffectiveDeptId() }
    const res = await fetchApprovalTasks(params)
    chatStore.setApprovalTasks(res.data.items)
  }

  const submitApproval = async (decision: 'approved' | 'rejected') => {
    if (!selectedApprovalTask.value) {
      return
    }
    try {
      chatStore.setApprovalSubmitting(true)
      const task = selectedApprovalTask.value
      const params = chatStore.canViewAllDepartments()
        ? { include_all: true, dept_id: chatStore.scopeDeptId || undefined }
        : { dept_id: chatStore.getEffectiveDeptId() }
      const res = await resumeApprovalTask({
        execution_id: task.execution_id,
        go_approval_id: task.go_approval_id,
        decision,
        comment: approvalComment.value.trim() || undefined,
      })
      const executionRes = await fetchExecution(task.execution_id, params)
      chatStore.setLatestExecution(executionRes.data)
      executionStream.start(task.execution_id)
        approvalComment.value = ''
        await loadApprovalTasks()
        if (chatStore.currentSessionId) {
          const messagesRes = await fetchChatMessages(chatStore.currentSessionId, params)
          chatStore.setMessages(messagesRes.data.items)
        }
      ElMessage.success(decision === 'approved' ? '审批已通过，执行继续进行。' : '审批已驳回，执行已终止。')
      return res.data
    } catch (error) {
      ElMessage.error(`提交审批失败：${String(error)}`)
      return null
    } finally {
      chatStore.setApprovalSubmitting(false)
    }
  }

  return {
    approvalTasks,
    approvalComment,
    selectedApprovalTask,
    loadApprovalTasks,
    submitApproval,
    selectApprovalTask: chatStore.setSelectedApprovalTask,
    approvalSubmitting: computed(() => chatStore.approvalSubmitting),
  }
}
