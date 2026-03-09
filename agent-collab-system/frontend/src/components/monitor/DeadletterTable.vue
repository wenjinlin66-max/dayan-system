<template>
  <div class="rounded-2xl border border-slate-800 bg-slate-900 p-4 min-h-[280px]">
    <div class="mb-3 text-sm text-slate-400">死信 / 异常任务</div>
    <VTableWrapper />
  </div>
</template>

<script setup lang="ts">
import VTableWrapper from '@/components/shared/VTableWrapper.vue'
</script>
