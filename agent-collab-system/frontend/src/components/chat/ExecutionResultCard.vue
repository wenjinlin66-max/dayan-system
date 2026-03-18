<template>
  <div class="rounded-[24px] border border-emerald-200 bg-[linear-gradient(180deg,#f2fff8_0%,#ebfff5_100%)] p-4 shadow-sm shadow-emerald-100/60">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-emerald-600/80">执行结果</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">执行状态回传</div>
      </div>
      <div class="flex items-center gap-2">
        <div v-if="execution" class="rounded-full border border-emerald-200 bg-white px-2.5 py-1 text-[11px] text-emerald-700">
          {{ execution.status }}
        </div>
        <el-button size="small" plain type="success" @click="resultDialogVisible = true">查看详情</el-button>
      </div>
    </div>
    <div v-if="chatStore.canViewAllDepartments()" class="mb-3">
      <el-select v-model="filterDeptId" class="w-full" placeholder="筛选执行结果所属部门">
        <el-option label="全部部门" value="" />
        <el-option v-for="item in deptOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </div>
    <div v-if="!execution" class="text-sm text-slate-500">当前部门对话框还没有新的 execution 回传。</div>
    <div v-else class="space-y-3 text-sm text-slate-700">
      <div class="space-y-2 rounded-[18px] border border-white/80 bg-white/75 p-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="text-sm font-semibold text-slate-900">{{ statusLabel }}</div>
            <div class="mt-1 text-xs leading-5 text-slate-500">{{ summaryText }}</div>
          </div>
          <div class="rounded-full border px-2.5 py-1 text-[11px]" :class="statusBadgeClass">{{ execution.status }}</div>
        </div>
        <div class="grid gap-2 text-xs text-slate-500 md:grid-cols-2">
          <div>execution_id: {{ execution.execution_id }}</div>
          <div>workflow_id: {{ execution.workflow_id }}</div>
          <div>dept_id: {{ execution.dept_id }}</div>
          <div>current_node: {{ execution.current_node || '-' }}</div>
        </div>
      </div>
    </div>

    <el-dialog v-model="resultDialogVisible" width="760px" align-center destroy-on-close>
      <template #header>
        <div>
          <div class="text-[11px] uppercase tracking-[0.22em] text-emerald-600/80">执行结果中心</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">当前执行结果详情</div>
        </div>
      </template>

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
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { useChatStore } from '@/store/chat'
import { ERP_DEPARTMENT_OPTIONS } from '@/utils/erpDepartments'
const chatStore = useChatStore()
const deptOptions = ERP_DEPARTMENT_OPTIONS.filter((item) => item.value !== 'ceo')
const resultDialogVisible = ref(false)
const filterDeptId = computed({
  get: () => chatStore.executionFilterDeptId,
  set: (value: string) => {
    chatStore.setExecutionFilterDeptId(value)
  },
})
const execution = computed(() => {
  if (chatStore.canViewAllDepartments() && filterDeptId.value && chatStore.latestExecutionByDept[filterDeptId.value]) {
    return chatStore.latestExecutionByDept[filterDeptId.value]
  }
  return chatStore.latestExecution
})
const statusLabel = computed(() => {
  const status = execution.value?.status
  if (status === 'finished') return '执行已完成'
  if (status === 'waiting_approval') return '执行等待审批'
  if (status === 'failed') return '执行失败'
  if (status === 'cancelled') return '执行已终止'
  return '执行进行中'
})

const summaryText = computed(() => {
  const finalOutput = execution.value?.final_output
  if (!finalOutput || typeof finalOutput !== 'object') {
    return '当前展示执行状态与基础结果，详细链路已收口到运行历史中。'
  }
  const decisionOutputs = finalOutput.decision_outputs
  if (decisionOutputs && typeof decisionOutputs === 'object') {
    const firstDecision = Object.values(decisionOutputs as Record<string, Record<string, unknown>>)[0]
    if (firstDecision && typeof firstDecision === 'object' && typeof firstDecision.decision_summary === 'string' && firstDecision.decision_summary) {
      return firstDecision.decision_summary
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
</script>
