<template>
  <div class="rounded-[24px] border border-emerald-200 bg-[linear-gradient(180deg,#f2fff8_0%,#ebfff5_100%)] p-4 shadow-sm shadow-emerald-100/60">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-emerald-600/80">执行结果</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">执行状态回传</div>
      </div>
      <div v-if="execution" class="rounded-full border border-emerald-200 bg-white px-2.5 py-1 text-[11px] text-emerald-700">
        {{ execution.status }}
      </div>
    </div>
    <div v-if="!execution" class="text-sm text-slate-500">当前部门对话框还没有新的 execution 回传。</div>
    <div v-else class="space-y-3 text-sm text-slate-700">
      <div class="space-y-1">
        <div>execution_id: {{ execution.execution_id }}</div>
        <div>status: {{ execution.status }}</div>
        <div>current_node: {{ execution.current_node || '-' }}</div>
        <div>workflow_id: {{ execution.workflow_id }}</div>
        <div>dept_id: {{ execution.dept_id }}</div>
      </div>

      <div v-if="sensorOutputs.length > 0" class="space-y-2 rounded-[18px] border border-white/80 bg-white/75 p-3">
        <div class="text-[11px] uppercase tracking-[0.2em] text-emerald-700/80">感知输出</div>
        <div
          v-for="item in sensorOutputs"
          :key="item.nodeId"
          class="rounded-2xl border border-emerald-100 bg-emerald-50/70 px-3 py-2"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="font-medium text-slate-900">{{ item.nodeId }}</div>
            <div class="text-xs text-emerald-700">{{ item.matched ? '已命中' : '未命中' }}</div>
          </div>
          <div class="mt-1 text-xs leading-5 text-slate-600">
            输出事件：{{ item.outputEventName || '-' }} · 来源匹配：{{ item.sourceMatched ? '是' : '否' }} · 条件匹配：{{ item.conditionMatched ? '是' : '否' }}
          </div>
          <pre class="mt-2 overflow-x-auto rounded-xl bg-slate-950 px-3 py-2 text-[11px] leading-5 text-slate-100">{{ item.payloadText }}</pre>
        </div>
      </div>

      <div v-if="decisionOutputs.length > 0" class="space-y-2 rounded-[18px] border border-white/80 bg-white/75 p-3">
        <div class="text-[11px] uppercase tracking-[0.2em] text-emerald-700/80">决策输出</div>
        <div
          v-for="item in decisionOutputs"
          :key="item.nodeId"
          class="rounded-2xl border border-emerald-100 bg-emerald-50/70 px-3 py-2"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="font-medium text-slate-900">{{ item.nodeId }}</div>
            <div class="text-xs text-emerald-700">{{ item.mode }} · {{ item.riskLevel }}</div>
          </div>
          <div class="mt-1 text-xs leading-5 text-slate-600">{{ item.summary }}</div>
          <pre class="mt-2 overflow-x-auto rounded-xl bg-slate-950 px-3 py-2 text-[11px] leading-5 text-slate-100">{{ item.payloadText }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useChatStore } from '@/store/chat'
const chatStore = useChatStore()
const execution = computed(() => chatStore.latestExecution)
const sensorOutputs = computed(() => {
  const rawOutputs = execution.value?.final_output?.sensor_outputs
  if (!rawOutputs || typeof rawOutputs !== 'object') {
    return []
  }

  return Object.entries(rawOutputs as Record<string, Record<string, unknown>>).map(([nodeId, value]) => ({
    nodeId,
    matched: Boolean(value?.matched),
    sourceMatched: Boolean(value?.source_matched),
    conditionMatched: Boolean(value?.condition_matched),
    outputEventName: typeof value?.output_event_name === 'string' ? value.output_event_name : '',
    payloadText: JSON.stringify(value?.payload ?? {}, null, 2),
  }))
})

const decisionOutputs = computed(() => {
  const rawOutputs = execution.value?.final_output?.decision_outputs
  if (!rawOutputs || typeof rawOutputs !== 'object') {
    return []
  }

  return Object.entries(rawOutputs as Record<string, Record<string, unknown>>).map(([nodeId, value]) => ({
    nodeId,
    mode: typeof value?.decision_mode === 'string' ? value.decision_mode : 'unknown',
    riskLevel: typeof value?.risk_level === 'string' ? value.risk_level : 'unknown',
    summary: typeof value?.decision_summary === 'string' ? value.decision_summary : '无摘要',
    payloadText: JSON.stringify(value?.decision_payload ?? {}, null, 2),
  }))
})
</script>
