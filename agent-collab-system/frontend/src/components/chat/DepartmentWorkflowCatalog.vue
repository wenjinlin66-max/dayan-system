<template>
  <div class="rounded-[24px] border border-slate-200/80 bg-white/96 p-4 shadow-[0_18px_40px_rgba(148,163,184,0.10)]">
    <div class="mb-3 flex items-center justify-between">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">部门流程目录</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">{{ chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments' ? '按部门 / workflow 分类查看' : '按 workflow 分类查看' }}</div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs text-slate-500">{{ catalog.length }} 条</span>
        <el-button size="small" plain @click="catalogVisible = true">打开流程目录</el-button>
      </div>
    </div>

    <div class="space-y-3">
      <section v-for="group in groupedCatalog" :key="group.category" class="rounded-[22px] border border-slate-200 bg-slate-50/70 p-3">
        <div class="mb-3 flex items-center justify-between">
          <div class="text-sm font-semibold text-slate-900">{{ group.label }}</div>
          <span class="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-500">{{ group.items.length }} 条</span>
        </div>

        <div class="space-y-2">
          <div v-for="item in group.items" :key="item.workflow_id" class="rounded-2xl border border-slate-200 bg-white px-3 py-3 text-sm">
            <div class="font-medium text-slate-900">{{ item.title }}</div>
            <div class="mt-1 text-xs text-slate-500">{{ item.summary }}</div>
            <div class="mt-3 flex flex-wrap gap-2">
              <span v-if="item.required_inputs?.length" class="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-[11px] text-amber-700">
                需补 {{ item.required_inputs.length }} 个参数
              </span>
            </div>
            <WorkflowParameterCard
              v-if="expandedWorkflowId === item.workflow_id && item.required_inputs?.length"
              class="mt-3"
              :workflow="item"
              source="catalog"
            />
            <div class="mt-3 flex flex-wrap gap-2">
              <el-button v-if="canStartWorkflow(item)" size="small" plain :loading="startingWorkflowId === item.workflow_id" @click="startWorkflow(item)">
                {{ item.required_inputs?.length ? '填写参数并启动' : '启动该流程' }}
              </el-button>
              <el-button size="small" @click="openHistory(item)">执行历史</el-button>
            </div>
          </div>
        </div>
      </section>

      <div v-if="catalog.length === 0" class="text-xs text-slate-500">当前部门还没有已发布 workflow。</div>
    </div>

    <WorkflowExecutionHistoryDialog
      :visible="historyVisible"
      :loading="historyLoading"
      :title="historyTitle"
      :items="historyItems"
      @close="historyVisible = false"
    />

    <el-dialog v-model="catalogVisible" width="980px" align-center destroy-on-close>
      <template #header>
        <div>
          <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">部门流程目录</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">按部门 / workflow 类型总览</div>
        </div>
      </template>

      <div class="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <section v-for="group in groupedCatalog" :key="`dialog-${group.category}`" class="rounded-[22px] border border-slate-200 bg-slate-50/70 p-4">
          <div class="mb-3 flex items-center justify-between">
            <div class="text-sm font-semibold text-slate-900">{{ group.label }}</div>
            <span class="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-500">{{ group.items.length }} 条</span>
          </div>

          <div class="grid gap-3 md:grid-cols-2">
            <div v-for="item in group.items" :key="`dialog-${item.workflow_id}`" class="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-sm">
              <div class="font-medium text-slate-900">{{ item.title }}</div>
              <div class="mt-1 text-xs leading-5 text-slate-500">{{ item.summary }}</div>
              <div class="mt-3 flex flex-wrap gap-2">
                <span v-if="item.required_inputs?.length" class="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-[11px] text-amber-700">
                  需补 {{ item.required_inputs.length }} 个参数
                </span>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <el-button v-if="canStartWorkflow(item)" size="small" plain :loading="startingWorkflowId === item.workflow_id" @click="startWorkflow(item)">
                  {{ item.required_inputs?.length ? '填写参数并启动' : '启动该流程' }}
                </el-button>
                <el-button size="small" @click="openHistory(item)">执行历史</el-button>
              </div>
            </div>
          </div>
        </section>

        <div v-if="catalog.length === 0" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-sm text-slate-500">
          当前部门还没有已发布 workflow。
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchWorkflowExecutionHistory } from '@/api/executions'
import WorkflowExecutionHistoryDialog from '@/components/shared/WorkflowExecutionHistoryDialog.vue'
import { useChatSession } from '@/composables/useChatSession'
import { useChatStore } from '@/store/chat'
import type { WorkflowExecutionHistoryItem } from '@/types/execution'
import type { WorkflowCatalogItem } from '@/types/chat'
import { getWorkflowCategoryLabel } from '@/utils/workflowCategory'
import WorkflowParameterCard from './WorkflowParameterCard.vue'

const chatStore = useChatStore()
const catalog = computed(() => chatStore.catalog)
const startingWorkflowId = computed(() => chatStore.startingWorkflowId)
const { startSelectedWorkflow } = useChatSession()
const expandedWorkflowId = ref('')
const historyVisible = ref(false)
const historyLoading = ref(false)
const historyTitle = ref('')
const historyItems = ref<WorkflowExecutionHistoryItem[]>([])
const catalogVisible = ref(false)

const resolveHistoryParams = () => {
  if (chatStore.canViewAllDepartments()) {
    if (chatStore.scopeMode === 'all_departments') {
      return {
        include_all: true,
        dept_id: chatStore.scopeDeptId || undefined,
      }
    }
    return {
      dept_id: chatStore.scopeDeptId || chatStore.getEffectiveDeptId(),
    }
  }
  return {
    dept_id: chatStore.getEffectiveDeptId(),
  }
}

const groupedCatalog = computed(() => {
  const groups = new Map<string, WorkflowCatalogItem[]>()
  catalog.value.forEach((item) => {
    const groupKey = chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments' ? `${item.dept_id}::${item.category}` : item.category
    groups.set(groupKey, [...(groups.get(groupKey) ?? []), item])
  })
  return Array.from(groups.entries()).map(([category, items]) => ({
    category,
    label: chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments'
      ? `${items[0]?.dept_id || ''} · ${getWorkflowCategoryLabel(category.split('::').pop() || category)}`
      : getWorkflowCategoryLabel(category),
    items,
  }))
})

const canStartWorkflow = (workflow: WorkflowCatalogItem) => workflow.category === 'dialog_trigger'

const startWorkflow = async (workflow: WorkflowCatalogItem) => {
  if (!canStartWorkflow(workflow)) {
    return
  }
  if (workflow.required_inputs?.length) {
    expandedWorkflowId.value = expandedWorkflowId.value === workflow.workflow_id ? '' : workflow.workflow_id
    return
  }
  await startSelectedWorkflow(workflow.workflow_id, 'catalog')
}

const openHistory = async (workflow: WorkflowCatalogItem) => {
  historyVisible.value = true
  historyLoading.value = true
  historyTitle.value = `${workflow.title} · 部门执行历史`
  try {
    const response = await fetchWorkflowExecutionHistory(workflow.workflow_id, resolveHistoryParams())
    historyItems.value = response.data.items
  } catch (error) {
    historyItems.value = []
    ElMessage.error(error instanceof Error ? error.message : `加载执行历史失败：${String(error)}`)
  } finally {
    historyLoading.value = false
  }
}
</script>
