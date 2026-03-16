<template>
  <el-dialog :model-value="visible" width="980px" destroy-on-close align-center @close="emit('close')">
    <template #header>
      <div>
        <div class="text-[11px] uppercase tracking-[0.24em] text-sky-700/80">Workflow Execution History</div>
        <div class="mt-1 text-xl font-semibold text-slate-900">{{ title || '工作流执行历史' }}</div>
      </div>
    </template>

    <div v-loading="loading" class="max-h-[72vh] overflow-y-auto pr-1">
      <div v-if="groupedItems.length > 0" class="space-y-4">
        <section v-for="group in groupedItems" :key="group.type" class="rounded-[22px] border border-slate-200 bg-slate-50/70 p-4">
          <div class="mb-3 flex items-center justify-between gap-3">
            <div>
              <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">执行类型</div>
              <div class="mt-1 text-base font-semibold text-slate-900">{{ group.type }}</div>
            </div>
            <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">{{ group.items.length }} 条</span>
          </div>

          <div class="space-y-3">
            <article v-for="item in group.items" :key="item.execution_id" class="rounded-[18px] border border-slate-200 bg-white p-4 shadow-sm">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div class="text-sm font-semibold text-slate-900">{{ item.execution_id }}</div>
                  <div class="mt-1 text-xs text-slate-500">workflow: {{ item.workflow_name }} · workflow_id: {{ item.workflow_id }}</div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] text-slate-600">{{ item.status }}</span>
                  <span
                    class="rounded-full px-2.5 py-1 text-[11px] font-medium"
                    :class="resultStatusClass(item.result_status)"
                  >
                    {{ resultStatusLabel(item.result_status) }}
                  </span>
                </div>
              </div>

              <div class="mt-3 grid gap-3 md:grid-cols-3">
                <div class="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700">
                  <div class="text-[11px] uppercase tracking-[0.14em] text-slate-400">执行任务</div>
                  <div class="mt-1 font-medium text-slate-900">{{ item.task_summary }}</div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700">
                  <div class="text-[11px] uppercase tracking-[0.14em] text-slate-400">执行对象</div>
                  <div class="mt-1 font-medium text-slate-900">{{ item.target_summary }}</div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700">
                  <div class="text-[11px] uppercase tracking-[0.14em] text-slate-400">执行时间</div>
                  <div class="mt-1 font-medium text-slate-900">{{ formatTime(item.started_at) }}</div>
                </div>
              </div>

              <div class="mt-3 rounded-[18px] border border-emerald-100 bg-gradient-to-r from-emerald-50 via-white to-sky-50 px-4 py-3">
                <div class="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div class="text-[11px] uppercase tracking-[0.16em] text-emerald-700/70">执行结果</div>
                    <div class="mt-1 text-sm font-medium text-slate-900">{{ item.result_summary || '暂无执行结果摘要' }}</div>
                  </div>
                  <span
                    class="rounded-full px-3 py-1 text-xs font-medium"
                    :class="resultStatusClass(item.result_status)"
                  >
                    {{ resultStatusLabel(item.result_status) }}
                  </span>
                </div>

                <div v-if="item.result_details?.length" class="mt-3 grid gap-2 md:grid-cols-2">
                  <div
                    v-for="detail in item.result_details"
                    :key="detail"
                    class="rounded-2xl border border-white/80 bg-white/85 px-3 py-2 text-sm text-slate-700 shadow-sm"
                  >
                    {{ detail }}
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>
      </div>

      <div v-else class="rounded-[22px] border border-dashed border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500">
        当前没有可查看的执行历史。
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { WorkflowExecutionHistoryItem } from '@/types/execution'

const props = defineProps<{
  visible: boolean
  loading?: boolean
  title?: string
  items: WorkflowExecutionHistoryItem[]
}>()

const emit = defineEmits<{
  close: []
}>()

const groupedItems = computed(() => {
  const groups = new Map<string, WorkflowExecutionHistoryItem[]>()
  props.items.forEach((item) => {
    groups.set(item.execution_type, [...(groups.get(item.execution_type) ?? []), item])
  })
  return Array.from(groups.entries()).map(([type, items]) => ({ type, items }))
})

const formatTime = (value?: string | null) => {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('zh-CN', { hour12: false })
}

const resultStatusLabel = (value?: string | null) => {
  if (value === 'succeeded') {
    return '执行成功'
  }
  if (value === 'failed') {
    return '执行失败'
  }
  if (value === 'waiting_approval') {
    return '等待审批'
  }
  return value || '结果未知'
}

const resultStatusClass = (value?: string | null) => {
  if (value === 'succeeded') {
    return 'border border-emerald-200 bg-emerald-50 text-emerald-700'
  }
  if (value === 'failed') {
    return 'border border-rose-200 bg-rose-50 text-rose-700'
  }
  if (value === 'waiting_approval') {
    return 'border border-amber-200 bg-amber-50 text-amber-700'
  }
  return 'border border-slate-200 bg-slate-50 text-slate-600'
}
</script>
