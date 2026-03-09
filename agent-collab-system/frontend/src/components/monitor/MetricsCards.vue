<template>
  <div class="grid grid-cols-4 gap-4">
    <div v-for="metric in metrics" :key="metric" class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <div class="text-sm text-slate-400">{{ metric }}</div>
      <div class="mt-2 text-2xl font-semibold">--</div>
    </div>
  </div>
</template>

<script setup lang="ts">
const metrics = ['QPS', '失败率', '超时数', '待审批数']
</script>
