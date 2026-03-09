<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-4">
    <h1 class="text-2xl font-semibold">智能体协同监控工作台</h1>
    <MetricsCards />
    <div class="grid grid-cols-2 gap-4">
      <ExecutionTable />
      <DeadletterTable />
    </div>
    <AlertPanel />
  </div>
</template>

<script setup lang="ts">
import AlertPanel from '@/components/monitor/AlertPanel.vue'
import DeadletterTable from '@/components/monitor/DeadletterTable.vue'
import ExecutionTable from '@/components/monitor/ExecutionTable.vue'
import MetricsCards from '@/components/monitor/MetricsCards.vue'
</script>
