<template>
  <div class="rounded-[24px] border border-indigo-200 bg-[linear-gradient(180deg,#f7f8ff_0%,#eef4ff_100%)] p-4 shadow-[0_18px_40px_rgba(99,102,241,0.10)]">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-indigo-600/80">中心工作台</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">审批任务与执行结果查看</div>
      </div>
      <div class="text-xs text-slate-500">审批 {{ approvalTasks.length }} 项 · 结果 {{ execution ? '1 条' : '0 条' }}</div>
    </div>

    <div class="space-y-3">
      <div class="grid gap-3 md:grid-cols-2">
        <div class="rounded-2xl border border-amber-200 bg-white/80 p-3">
          <div class="text-xs uppercase tracking-[0.18em] text-amber-600/80">审批任务</div>
          <div class="mt-2 text-sm font-semibold text-slate-900">{{ approvalTasks.length > 0 ? `${approvalTasks.length} 项待处理` : '当前无待处理审批' }}</div>
          <div class="mt-1 text-xs leading-5 text-slate-500">{{ approvalTasks.length > 0 ? approvalTasks[0].title : '这里只集中查看审批任务，实际流程触发仍以对话型智能体为主。' }}</div>
        </div>
        <div class="rounded-2xl border border-emerald-200 bg-white/80 p-3">
          <div class="text-xs uppercase tracking-[0.18em] text-emerald-600/80">执行结果</div>
          <div class="mt-2 text-sm font-semibold text-slate-900">{{ statusLabel }}</div>
          <div class="mt-1 text-xs leading-5 text-slate-500">这里只查看各类 workflow 的执行结果；除对话型 workflow 外，其它类型当前不在这里直接启动。</div>
        </div>
      </div>

      <el-button class="w-full" type="primary" @click="openCenter()">打开中心工作台</el-button>
    </div>

    <el-dialog v-model="centerVisible" width="980px" align-center destroy-on-close>
      <template #header>
        <div>
          <div class="text-[11px] uppercase tracking-[0.22em] text-indigo-600/80">中心工作台</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">审批任务 / 执行结果查看</div>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="operations-center-tabs">
        <el-tab-pane label="审批任务" name="approvals">
          <div class="space-y-4">
            <div v-if="chatStore.canViewAllDepartments()" class="max-w-[280px]">
              <el-select v-model="filterDeptId" class="w-full" placeholder="筛选审批所属部门">
                <el-option label="全部部门" value="" />
                <el-option v-for="item in deptOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>

            <div class="grid gap-4 md:grid-cols-[280px_minmax(0,1fr)]">
              <div class="space-y-3">
                <div class="text-xs uppercase tracking-[0.18em] text-slate-500">审批任务列表</div>
                <div v-if="approvalTasks.length === 0" class="rounded-2xl border border-dashed border-amber-200 bg-amber-50/60 px-4 py-8 text-center text-sm text-slate-500">
                  当前没有待处理审批。
                </div>
                <div v-else class="max-h-[460px] space-y-2 overflow-y-auto pr-1">
                  <button
                    v-for="task in approvalTasks"
                    :key="task.approval_task_id"
                    class="w-full rounded-2xl border px-4 py-3 text-left transition"
                    :class="selectedApprovalTask?.approval_task_id === task.approval_task_id ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-white hover:bg-slate-50'"
                    @click="selectApprovalTask(task.approval_task_id)"
                  >
                    <div class="truncate text-sm font-semibold text-slate-900">{{ task.title }}</div>
                    <div class="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{{ task.summary }}</div>
                    <div class="mt-2 text-[11px] text-slate-400">{{ task.dept_id }} · {{ task.workflow_id }}</div>
                  </button>
                </div>
              </div>

              <div v-if="selectedApprovalTask" class="space-y-4">
                <ApprovalCard :task="selectedApprovalTask" />
                <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                  <div class="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">审批意见</div>
                  <el-input v-model="approvalComment" type="textarea" :rows="5" placeholder="输入审批意见（可选）" />
                </div>
                <div class="flex items-center justify-end gap-3">
                  <el-button type="danger" :loading="approvalSubmitting" @click="handleSubmit('rejected')">驳回</el-button>
                  <el-button type="success" :loading="approvalSubmitting" @click="handleSubmit('approved')">同意</el-button>
                </div>
              </div>
              <div v-else class="flex items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-16 text-sm text-slate-500">
                请选择左侧一个审批任务查看详情。
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="执行结果" name="results">
          <div class="space-y-4">
            <div v-if="chatStore.canViewAllDepartments()" class="max-w-[280px]">
              <el-select v-model="executionFilterDeptId" class="w-full" placeholder="筛选执行结果所属部门">
                <el-option label="全部部门" value="" />
                <el-option v-for="item in deptOptions" :key="`exec-${item.value}`" :label="item.label" :value="item.value" />
              </el-select>
            </div>

            <div v-if="!execution" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-sm text-slate-500">
              当前还没有 execution 回传。
            </div>
            <div v-else class="space-y-4">
              <div class="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <div class="text-base font-semibold text-slate-900">{{ statusLabel }}</div>
                    <div class="mt-1 text-sm leading-6 text-slate-600">{{ summaryText }}</div>
                  </div>
                  <div class="rounded-full border px-2.5 py-1 text-[11px]" :class="statusBadgeClass">{{ execution.status }}</div>
                </div>
              </div>

              <div class="grid gap-3 md:grid-cols-2">
                <div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                  <div class="text-xs uppercase tracking-[0.18em] text-slate-500">执行标识</div>
                  <div class="mt-2 break-all">{{ execution.execution_id }}</div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                  <div class="text-xs uppercase tracking-[0.18em] text-slate-500">工作流</div>
                  <div class="mt-2 break-all">{{ execution.workflow_id }}</div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                  <div class="text-xs uppercase tracking-[0.18em] text-slate-500">所属部门</div>
                  <div class="mt-2">{{ execution.dept_id }}</div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                  <div class="text-xs uppercase tracking-[0.18em] text-slate-500">当前节点</div>
                  <div class="mt-2 break-all">{{ execution.current_node || '-' }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { useApprovals } from '@/composables/useApprovals'
import { useChatStore } from '@/store/chat'
import { ERP_DEPARTMENT_OPTIONS } from '@/utils/erpDepartments'
import ApprovalCard from './ApprovalCard.vue'

const chatStore = useChatStore()
const { approvalTasks, approvalComment, selectedApprovalTask, loadApprovalTasks, submitApproval, selectApprovalTask, approvalSubmitting } = useApprovals()

const centerVisible = ref(false)
const activeTab = ref<'approvals' | 'results'>('approvals')
const deptOptions = ERP_DEPARTMENT_OPTIONS.filter((item) => item.value !== 'ceo')

const filterDeptId = computed({
  get: () => chatStore.approvalFilterDeptId,
  set: async (value: string) => {
    chatStore.setApprovalFilterDeptId(value)
    if (value) {
      chatStore.applyScopeDeptId(value)
    }
    await loadApprovalTasks()
  },
})

const executionFilterDeptId = computed({
  get: () => chatStore.executionFilterDeptId,
  set: (value: string) => {
    chatStore.setExecutionFilterDeptId(value)
  },
})

const execution = computed(() => {
  if (chatStore.canViewAllDepartments() && executionFilterDeptId.value && chatStore.latestExecutionByDept[executionFilterDeptId.value]) {
    return chatStore.latestExecutionByDept[executionFilterDeptId.value]
  }
  return chatStore.latestExecution
})

const statusLabel = computed(() => {
  if (!execution.value) return '暂无执行结果'
  const status = execution.value?.status
  if (status === 'finished') return '执行已完成'
  if (status === 'waiting_approval') return '执行等待审批'
  if (status === 'failed') return '执行失败'
  if (status === 'cancelled') return '执行已终止'
  return '执行进行中'
})

const summaryText = computed(() => {
  if (!execution.value) {
    return '当前还没有 execution 回传。'
  }
  const finalOutput = execution.value?.final_output
  if (!finalOutput || typeof finalOutput !== 'object') {
    return '当前展示执行状态与基础结果，详细链路已收口到运行历史中。'
  }
  const decisionOutputs = finalOutput.decision_outputs
  if (decisionOutputs && typeof decisionOutputs === 'object') {
    const firstDecision = Object.values(decisionOutputs as Record<string, Record<string, unknown>>)[0]
    if (firstDecision && typeof firstDecision === 'object') {
      const summary = (firstDecision as Record<string, unknown>).decision_summary
      if (typeof summary === 'string' && summary) {
        return summary
      }
    }
  }
  const toolOutputs = finalOutput.tool_outputs
  if (toolOutputs && typeof toolOutputs === 'object') {
    const firstTool = Object.values(toolOutputs as Record<string, Record<string, unknown>>)[0]
    const result = firstTool?.result
    if (result && typeof result === 'object') {
      const summary = (result as Record<string, unknown>).summary
      if (typeof summary === 'string' && summary) {
        return summary
      }
    }
  }
  return '当前展示执行状态与基础结果，详细链路已收口到运行历史中。'
})

const statusBadgeClass = computed(() => {
  const status = execution.value?.status
  if (status === 'finished') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (status === 'waiting_approval') return 'border-amber-200 bg-amber-50 text-amber-700'
  if (status === 'failed' || status === 'cancelled') return 'border-rose-200 bg-rose-50 text-rose-700'
  return 'border-sky-200 bg-sky-50 text-sky-700'
})

onMounted(async () => {
  await loadApprovalTasks()
})

const openCenter = (tab: 'approvals' | 'results' = 'approvals') => {
  activeTab.value = tab
  if (approvalTasks.value.length > 0 && !selectedApprovalTask.value) {
    selectApprovalTask(approvalTasks.value[0].approval_task_id)
  }
  approvalComment.value = ''
  centerVisible.value = true
}

const handleSubmit = async (decision: 'approved' | 'rejected') => {
  const result = await submitApproval(decision)
  if (result) {
    centerVisible.value = false
  }
}
</script>
