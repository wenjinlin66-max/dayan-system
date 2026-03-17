<template>
  <div class="rounded-[24px] border border-amber-200 bg-[linear-gradient(180deg,#fffaf1_0%,#fff5e8_100%)] p-4 shadow-[0_18px_40px_rgba(245,158,11,0.10)]">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-amber-600/80">审批工作区</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">{{ approvalTitle }}</div>
      </div>
      <div class="text-xs text-slate-500">待处理 {{ approvalTasks.length }} 项</div>
    </div>
    <div v-if="chatStore.canViewAllDepartments()" class="mb-3">
      <el-select v-model="filterDeptId" class="w-full" placeholder="筛选审批所属部门">
        <el-option label="全部部门" value="" />
        <el-option v-for="item in deptOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </div>
    <div v-if="approvalTasks.length === 0" class="rounded-xl border border-dashed border-amber-200 bg-white/70 px-4 py-8 text-center text-sm text-slate-500">
      当前没有待处理审批。
    </div>
    <div v-else class="space-y-3">
      <div class="flex flex-wrap gap-2">
        <el-button
          v-for="task in approvalTasks"
          :key="task.approval_task_id"
          size="small"
          :type="selectedApprovalTask?.approval_task_id === task.approval_task_id ? 'primary' : 'default'"
          @click="selectApprovalTask(task.approval_task_id)"
        >
          {{ task.title }}
        </el-button>
      </div>

      <div v-if="selectedApprovalTask" class="rounded-2xl border border-amber-200 bg-white/85 p-3 text-xs text-slate-500">归属部门：{{ selectedApprovalTask.dept_id }}</div>
      <ApprovalCard v-if="selectedApprovalTask" :task="selectedApprovalTask" />
      <el-input v-model="approvalComment" type="textarea" :rows="3" placeholder="输入审批意见" />
      <div class="flex gap-3">
        <el-button type="success" :loading="approvalSubmitting" @click="submitApproval('approved')">同意</el-button>
        <el-button type="danger" :loading="approvalSubmitting" @click="submitApproval('rejected')">驳回</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'

import ApprovalCard from './ApprovalCard.vue'
import { useApprovals } from '@/composables/useApprovals'
import { useChatStore } from '@/store/chat'
import { ERP_DEPARTMENT_OPTIONS } from '@/utils/erpDepartments'

const chatStore = useChatStore()
const { approvalTasks, approvalComment, selectedApprovalTask, loadApprovalTasks, submitApproval, selectApprovalTask, approvalSubmitting } = useApprovals()
const approvalTitle = computed(() => chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments' ? 'CEO 当前范围审批待办' : '当前部门审批待办')
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

onMounted(async () => {
  await loadApprovalTasks()
})
</script>
