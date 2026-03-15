<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#edf3fb_0%,#f8fbff_44%,#eef2f7_100%)] px-4 py-5 text-slate-900 md:px-6">
    <WorkspaceTopNav
      title="工作流查看区"
      description="查看当前部门有权限的 workflow，按正式 workflow 分类体系和发布状态查询。"
    />

    <div class="rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-[0_30px_80px_rgba(15,23,42,0.10)]">
      <div class="grid gap-4 lg:grid-cols-[1.4fr_0.8fr_0.9fr_0.8fr_auto]">
        <div>
          <div class="mb-1.5 text-[11px] uppercase tracking-[0.2em] text-slate-500">关键词搜索</div>
          <el-input v-model="keyword" placeholder="输入 workflow 名称或编码" clearable />
        </div>
        <div>
          <div class="mb-1.5 text-[11px] uppercase tracking-[0.2em] text-slate-500">发布状态</div>
          <el-select v-model="statusFilter" class="w-full">
            <el-option label="全部状态" value="all" />
            <el-option label="已发布" value="released" />
            <el-option label="仅草稿" value="draft" />
          </el-select>
        </div>
        <div>
          <div class="mb-1.5 text-[11px] uppercase tracking-[0.2em] text-slate-500">所属部门</div>
          <el-select v-model="deptFilter" class="w-full">
            <el-option label="全部部门" value="all" />
            <el-option v-for="item in workflowDeptOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div>
          <div class="mb-1.5 text-[11px] uppercase tracking-[0.2em] text-slate-500">触发逻辑分类</div>
          <el-select v-model="categoryFilter" class="w-full">
            <el-option label="全部分类" value="all" />
            <el-option v-for="item in WORKFLOW_TRIGGER_TYPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="flex items-end">
          <el-button @click="refresh">刷新列表</el-button>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap items-center gap-2">
        <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-500">共 {{ filteredWorkflows.length }} 条</span>
        <span class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-700">已发布 {{ releasedCount }} 条</span>
        <span class="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-700">草稿中 {{ draftCount }} 条</span>
        <span class="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs text-sky-700">当前按部门 → 触发逻辑查看流程（演示阶段可跨部门浏览）</span>
      </div>

      <div v-if="filteredWorkflows.length === 0" class="mt-8 rounded-[24px] border border-dashed border-slate-200 bg-slate-50 px-4 py-14 text-center text-sm text-slate-500">
        当前没有符合筛选条件的 workflow。
      </div>

      <div v-else class="mt-6 space-y-6">
        <section v-for="deptGroup in groupedWorkflows" :key="deptGroup.deptId" class="rounded-[26px] border border-slate-200/80 bg-slate-50/70 p-4">
          <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">所属部门</div>
              <div class="mt-1 text-lg font-semibold text-slate-950">{{ deptGroup.label }}</div>
            </div>
            <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">{{ deptGroup.total }} 条</span>
          </div>
          <div class="space-y-4">
            <section v-for="categoryGroup in deptGroup.categories" :key="`${deptGroup.deptId}-${categoryGroup.category}`" class="rounded-[22px] border border-slate-200 bg-white/80 p-4">
              <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">触发逻辑分类</div>
                  <div class="mt-1 text-base font-semibold text-slate-950">{{ categoryGroup.label }}</div>
                </div>
                <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">{{ categoryGroup.items.length }} 条</span>
              </div>
              <div class="grid gap-4 xl:grid-cols-2">
                <div v-for="item in categoryGroup.items" :key="item.workflow_id" class="rounded-[24px] border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fbff_100%)] p-5 shadow-sm shadow-slate-200/70">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="text-lg font-semibold text-slate-900">{{ item.name }}</div>
                  <div class="mt-1 text-sm text-slate-500">{{ item.code }}</div>
                </div>
                <span
                  class="rounded-full border px-2.5 py-1 text-[11px]"
                  :class="item.current_release_version ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'"
                >
                  {{ item.current_release_version ? '已发布' : '仅草稿' }}
                </span>
              </div>

              <div class="mt-4 grid gap-3 md:grid-cols-3">
                <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
                  <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">所属部门</div>
                  <div class="mt-1 font-medium text-slate-900">{{ item.owner_dept_id }}</div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
                  <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">草稿版本</div>
                  <div class="mt-1 font-medium text-slate-900">v{{ item.latest_draft_version ?? '-' }}</div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
                  <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">发布版本</div>
                  <div class="mt-1 font-medium text-slate-900">{{ item.current_release_version ? `v${item.current_release_version}` : '未发布' }}</div>
                </div>
              </div>

              <div class="mt-4 flex flex-wrap gap-3">
                <RouterLink :to="{ name: 'workflow-canvas', query: { workflowId: item.workflow_id } }">
                  <el-button>前往制作区</el-button>
                </RouterLink>
                <el-button @click="openHistory(item)">执行历史</el-button>
                <RouterLink :to="'/chat-workbench'">
                  <el-button type="primary" plain>前往对话区</el-button>
                </RouterLink>
                <el-button type="danger" plain @click="handleDeleteWorkflow(item.workflow_id)">删除工作流</el-button>
              </div>
            </div>
              </div>
            </section>
          </div>
        </section>
      </div>
    </div>

    <WorkflowExecutionHistoryDialog
      :visible="historyVisible"
      :loading="historyLoading"
      :title="historyTitle"
      :items="historyItems"
      @close="historyVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { fetchWorkflowExecutionHistory } from '@/api/executions'
import WorkspaceTopNav from '@/components/layout/WorkspaceTopNav.vue'
import WorkflowExecutionHistoryDialog from '@/components/shared/WorkflowExecutionHistoryDialog.vue'
import { deleteWorkflow, fetchWorkflows } from '@/api/workflows'
import type { WorkflowExecutionHistoryItem } from '@/types/execution'
import type { WorkflowSummary } from '@/types/workflow'
import { ERP_DEPARTMENT_OPTIONS, getDepartmentLabel } from '@/utils/erpDepartments'
import { getWorkflowCategoryLabel, WORKFLOW_TRIGGER_TYPE_OPTIONS } from '@/utils/workflowCategory'

const workflows = ref<WorkflowSummary[]>([])
const keyword = ref('')
const statusFilter = ref<'all' | 'released' | 'draft'>('all')
const deptFilter = ref('all')
const categoryFilter = ref('all')
const workflowDeptOptions = ERP_DEPARTMENT_OPTIONS.filter((item) => item.value !== 'ceo')
const historyVisible = ref(false)
const historyLoading = ref(false)
const historyTitle = ref('')
const historyItems = ref<WorkflowExecutionHistoryItem[]>([])

const refresh = async () => {
  const res = await fetchWorkflows({ include_all: true })
  workflows.value = res.data
}

const handleDeleteWorkflow = async (workflowId: string) => {
  try {
    await ElMessageBox.confirm('删除后该工作流将从查看区移除，确认继续？', '删除工作流', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  const item = workflows.value.find((entry) => entry.workflow_id === workflowId)
  await deleteWorkflow(workflowId, { dept_id: item?.owner_dept_id })
  await refresh()
  ElMessage.success('工作流已删除')
}

const openHistory = async (workflow: WorkflowSummary) => {
  historyVisible.value = true
  historyLoading.value = true
  historyTitle.value = `${workflow.name} · 执行历史`
  try {
    const response = await fetchWorkflowExecutionHistory(workflow.workflow_id, { include_all: true })
    historyItems.value = response.data.items
  } catch (error) {
    historyItems.value = []
    ElMessage.error(error instanceof Error ? error.message : `加载执行历史失败：${String(error)}`)
  } finally {
    historyLoading.value = false
  }
}

onMounted(async () => {
  await refresh()
})

const filteredWorkflows = computed(() => workflows.value.filter((item) => {
  const query = keyword.value.trim().toLowerCase()
  const matchesKeyword = !query || item.name.toLowerCase().includes(query) || item.code.toLowerCase().includes(query)
  const matchesStatus =
    statusFilter.value === 'all'
      ? true
      : statusFilter.value === 'released'
        ? Boolean(item.current_release_version)
        : !item.current_release_version
  const matchesDept = deptFilter.value === 'all' ? true : item.owner_dept_id === deptFilter.value
  const matchesCategory = categoryFilter.value === 'all' ? true : item.workflow_trigger_type === categoryFilter.value
  return matchesKeyword && matchesStatus && matchesDept && matchesCategory
}))

const groupedWorkflows = computed(() => {
  const groups = new Map<string, Map<string, WorkflowSummary[]>>()
  filteredWorkflows.value.forEach((item) => {
    const deptKey = item.owner_dept_id || 'unknown'
    const categoryKey = item.workflow_trigger_type || 'dialog_trigger'
    const categoryMap = groups.get(deptKey) ?? new Map<string, WorkflowSummary[]>()
    categoryMap.set(categoryKey, [...(categoryMap.get(categoryKey) ?? []), item])
    groups.set(deptKey, categoryMap)
  })
  return Array.from(groups.entries()).map(([deptId, categoryMap]) => ({
    deptId,
    label: getDepartmentLabel(deptId),
    total: Array.from(categoryMap.values()).reduce((sum, items) => sum + items.length, 0),
    categories: Array.from(categoryMap.entries()).map(([category, items]) => ({
      category,
      label: getWorkflowCategoryLabel(category),
      items,
    })),
  }))
})

const releasedCount = computed(() => workflows.value.filter((item) => Boolean(item.current_release_version)).length)
const draftCount = computed(() => workflows.value.filter((item) => !item.current_release_version).length)
</script>
