<template>
  <div class="space-y-4 rounded-[26px] border border-rose-200/80 bg-[linear-gradient(180deg,#fff8fb_0%,#fff1f5_100%)] p-5 shadow-[0_18px_45px_rgba(244,63,94,0.10)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-rose-600/80">审批节点</div>
        <div class="mt-1 text-base font-semibold text-slate-900">审批策略与超时处理</div>
      </div>
      <span class="rounded-full border border-rose-300 bg-white px-3 py-1 text-[11px] font-medium text-rose-700">approval</span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-rose-100/60 space-y-3">
      <div class="text-xs uppercase tracking-[0.22em] text-slate-500">审批配置</div>
      <el-input v-model="approvalTitle" placeholder="审批卡片标题" />
      <div class="grid gap-3 md:grid-cols-2">
        <el-input v-model="approvalPolicy" placeholder="审批策略，如 risk_based" />
        <el-input v-model="approverScope" placeholder="审批人范围，如 dept_manager" />
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-rose-100/60 space-y-3">
      <div class="text-xs uppercase tracking-[0.22em] text-slate-500">超时与兜底</div>
      <el-input v-model="timeoutAction" placeholder="超时动作，如 auto_reject / escalate" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApprovalNodeConfig } from '@/types/workflow'

const props = defineProps<{ modelValue: Record<string, unknown> }>()
const emit = defineEmits<{ 'update:modelValue': [value: ApprovalNodeConfig] }>()

const currentConfig = computed<ApprovalNodeConfig>(() => {
  const config = props.modelValue as ApprovalNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    approvalPolicy: config.approvalPolicy ?? '',
    approvalTitle: config.approvalTitle ?? '',
    approverScope: config.approverScope ?? '',
    timeoutAction: config.timeoutAction ?? '',
  }
})

const updateConfig = (patch: Partial<ApprovalNodeConfig>) => emit('update:modelValue', { ...currentConfig.value, ...patch })
const approvalPolicy = computed({ get: () => currentConfig.value.approvalPolicy ?? '', set: (value: string) => updateConfig({ approvalPolicy: value }) })
const approvalTitle = computed({ get: () => currentConfig.value.approvalTitle ?? '', set: (value: string) => updateConfig({ approvalTitle: value }) })
const approverScope = computed({ get: () => currentConfig.value.approverScope ?? '', set: (value: string) => updateConfig({ approverScope: value }) })
const timeoutAction = computed({ get: () => currentConfig.value.timeoutAction ?? '', set: (value: string) => updateConfig({ timeoutAction: value }) })
</script>
