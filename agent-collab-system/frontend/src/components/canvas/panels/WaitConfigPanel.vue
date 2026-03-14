<template>
  <div class="space-y-4 rounded-[26px] border border-indigo-200/80 bg-[linear-gradient(180deg,#fafbff_0%,#f2f5ff_100%)] p-5 shadow-[0_18px_45px_rgba(99,102,241,0.10)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-indigo-600/80">等待节点</div>
        <div class="mt-1 text-base font-semibold text-slate-900">等待条件与恢复事件</div>
      </div>
      <span class="rounded-full border border-indigo-300 bg-white px-3 py-1 text-[11px] font-medium text-indigo-700">wait</span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-indigo-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">等待方式</div>
      <div class="grid gap-3 md:grid-cols-2">
        <el-input v-model="waitMode" placeholder="等待模式，如 duration / event" />
        <el-input v-model="waitValue" placeholder="等待值，如 5m / low_stock.approved" />
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-indigo-100/60 space-y-3">
      <div class="text-xs uppercase tracking-[0.22em] text-slate-500">恢复触发</div>
      <el-input v-model="resumeEvent" placeholder="恢复事件键，如 approval.resume.replenishment" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { WaitNodeConfig } from '@/types/workflow'

const props = defineProps<{ modelValue: Record<string, unknown> }>()
const emit = defineEmits<{ 'update:modelValue': [value: WaitNodeConfig] }>()

const currentConfig = computed<WaitNodeConfig>(() => {
  const config = props.modelValue as WaitNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    waitMode: config.waitMode ?? '',
    waitValue: config.waitValue ?? '',
    resumeEvent: config.resumeEvent ?? '',
  }
})

const updateConfig = (patch: Partial<WaitNodeConfig>) => emit('update:modelValue', { ...currentConfig.value, ...patch })
const waitMode = computed({ get: () => currentConfig.value.waitMode ?? '', set: (value: string) => updateConfig({ waitMode: value }) })
const waitValue = computed({ get: () => currentConfig.value.waitValue ?? '', set: (value: string) => updateConfig({ waitValue: value }) })
const resumeEvent = computed({ get: () => currentConfig.value.resumeEvent ?? '', set: (value: string) => updateConfig({ resumeEvent: value }) })
</script>
