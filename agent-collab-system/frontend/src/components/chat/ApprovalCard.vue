<template>
  <div class="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-xs uppercase tracking-[0.22em] text-amber-300">审批任务</div>
        <div class="mt-2 text-base font-semibold text-slate-100">{{ task.title }}</div>
      </div>
      <span class="rounded-full border border-amber-400/30 bg-slate-950/40 px-2.5 py-1 text-[11px] text-amber-100">
        {{ task.status }}
      </span>
    </div>
    <div class="mt-3 text-sm leading-6 text-slate-300">{{ task.summary }}</div>
    <div class="mt-3 text-xs text-slate-500">execution_id: {{ task.execution_id }}</div>
  </div>
</template>

<script setup lang="ts">
import type { ApprovalTask } from '@/types/chat'

defineProps<{
  task: ApprovalTask
}>()
</script>
