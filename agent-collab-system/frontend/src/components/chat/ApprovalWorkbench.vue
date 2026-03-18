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
    <div class="space-y-3">
      <div v-if="approvalTasks.length === 0" class="rounded-xl border border-dashed border-amber-200 bg-white/70 px-4 py-8 text-center text-sm text-slate-500">
        当前没有待处理审批。
      </div>
      <div v-else class="rounded-2xl border border-amber-200 bg-white/80 p-3">
        <div class="space-y-2">
          <div
            v-for="task in previewTasks"
            :key="task.approval_task_id"
            class="rounded-xl border border-amber-100 bg-amber-50/60 px-3 py-2"
          >
            <div class="truncate text-sm font-medium text-slate-900">{{ task.title }}</div>
            <div class="mt-1 line-clamp-1 text-xs text-slate-500">{{ task.summary }}</div>
          </div>
        </div>
      </div>

      <el-button class="w-full" type="warning" plain @click="openApprovalCenter">
        打开总审批区
      </el-button>
    </div>

    <el-dialog v-model="approvalDialogVisible" width="920px" align-center destroy-on-close>
      <template #header>
        <div>
          <div class="text-[11px] uppercase tracking-[0.22em] text-amber-600/80">总审批区</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">审批任务中心</div>
        </div>
      </template>

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
        </div>
        <div v-else class="flex items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-16 text-sm text-slate-500">
          请选择左侧一个审批任务查看详情。
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-3">
          <el-button @click="approvalDialogVisible = false">取消</el-button>
          <el-button type="danger" :loading="approvalSubmitting" @click="handleSubmit('rejected')">驳回</el-button>
          <el-button type="success" :loading="approvalSubmitting" @click="handleSubmit('approved')">同意</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ApprovalCard from './ApprovalCard.vue'
import { useApprovals } from '@/composables/useApprovals'
import { useChatStore } from '@/store/chat'
import { ERP_DEPARTMENT_OPTIONS } from '@/utils/erpDepartments'

const chatStore = useChatStore()
const { approvalTasks, approvalComment, selectedApprovalTask, loadApprovalTasks, submitApproval, selectApprovalTask, approvalSubmitting } = useApprovals()
const approvalDialogVisible = ref(false)
const approvalTitle = computed(() => chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments' ? 'CEO 当前范围审批待办' : '当前部门审批待办')
const previewTasks = computed(() => approvalTasks.value.slice(0, 2))
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

const openApprovalDialog = (approvalTaskId: string) => {
  approvalComment.value = ''
  selectApprovalTask(approvalTaskId)
  approvalDialogVisible.value = true
}

const openApprovalCenter = () => {
  if (approvalTasks.value.length > 0 && !selectedApprovalTask.value) {
    selectApprovalTask(approvalTasks.value[0].approval_task_id)
  }
  approvalComment.value = ''
  approvalDialogVisible.value = true
}

const handleSubmit = async (decision: 'approved' | 'rejected') => {
  const result = await submitApproval(decision)
  if (result) {
    approvalDialogVisible.value = false
  }
}
</script>
