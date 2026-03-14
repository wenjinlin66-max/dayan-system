<template>
  <div class="rounded-[24px] border border-slate-200/80 bg-white/96 p-4 shadow-[0_18px_40px_rgba(148,163,184,0.10)]">
    <div class="mb-3 flex items-center justify-between">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">部门流程目录</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">按 workflow 分类查看</div>
      </div>
      <span class="text-xs text-slate-500">{{ catalog.length }} 条</span>
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
            <el-button class="mt-3" size="small" plain :loading="startingWorkflowId === item.workflow_id" @click="startWorkflow(item)">
              {{ item.required_inputs?.length ? '填写参数并启动' : '启动该流程' }}
            </el-button>
          </div>
        </div>
      </section>

      <div v-if="catalog.length === 0" class="text-xs text-slate-500">当前部门还没有已发布 workflow。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { useChatSession } from '@/composables/useChatSession'
import { useChatStore } from '@/store/chat'
import type { WorkflowCatalogItem } from '@/types/chat'
import { getWorkflowCategoryLabel } from '@/utils/workflowCategory'
import WorkflowParameterCard from './WorkflowParameterCard.vue'

const chatStore = useChatStore()
const catalog = computed(() => chatStore.catalog)
const startingWorkflowId = computed(() => chatStore.startingWorkflowId)
const { startSelectedWorkflow } = useChatSession()
const expandedWorkflowId = ref('')

const groupedCatalog = computed(() => {
  const groups = new Map<string, WorkflowCatalogItem[]>()
  catalog.value.forEach((item) => {
    groups.set(item.category, [...(groups.get(item.category) ?? []), item])
  })
  return Array.from(groups.entries()).map(([category, items]) => ({
    category,
    label: getWorkflowCategoryLabel(category),
    items,
  }))
})

const startWorkflow = async (workflow: WorkflowCatalogItem) => {
  if (workflow.required_inputs?.length) {
    expandedWorkflowId.value = expandedWorkflowId.value === workflow.workflow_id ? '' : workflow.workflow_id
    return
  }
  await startSelectedWorkflow(workflow.workflow_id, 'catalog')
}
</script>
