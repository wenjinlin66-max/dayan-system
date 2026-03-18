<template>
  <div class="rounded-2xl border border-amber-200 bg-amber-50/80 p-4 text-slate-700">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-xs uppercase tracking-[0.22em] text-amber-600/80">审批任务</div>
        <div class="mt-2 text-base font-semibold text-slate-900">{{ task.title }}</div>
      </div>
      <span class="rounded-full border border-amber-200 bg-white px-2.5 py-1 text-[11px] text-amber-700">
        {{ task.status }}
      </span>
    </div>
    <div class="mt-3 text-sm leading-6 text-slate-600">{{ task.summary }}</div>
    <div class="mt-3 space-y-1 text-xs text-slate-500">
      <div>execution_id: {{ task.execution_id }}</div>
      <div>workflow_id: {{ task.workflow_id }}</div>
      <div>dept_id: {{ task.dept_id }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ApprovalTask } from '@/types/chat'

defineProps<{
  task: ApprovalTask
}>()
</script>
