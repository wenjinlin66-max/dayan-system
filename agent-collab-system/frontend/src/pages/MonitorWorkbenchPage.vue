<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#edf3fb_0%,#f8fbff_44%,#eef2f7_100%)] p-6 text-slate-900 space-y-4">
    <WorkspaceTopNav
      title="监控区"
      description="查看执行状态、异常任务、死信与告警信息，后续作为监控型智能体的独立工作台。"
    />
    <div class="rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-[0_30px_80px_rgba(15,23,42,0.10)] space-y-4">
      <MetricsCards />
      <div class="grid grid-cols-2 gap-4">
      <ExecutionTable />
      <DeadletterTable />
      </div>
      <AlertPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import AlertPanel from '@/components/monitor/AlertPanel.vue'
import DeadletterTable from '@/components/monitor/DeadletterTable.vue'
import ExecutionTable from '@/components/monitor/ExecutionTable.vue'
import WorkspaceTopNav from '@/components/layout/WorkspaceTopNav.vue'
import MetricsCards from '@/components/monitor/MetricsCards.vue'
</script>
