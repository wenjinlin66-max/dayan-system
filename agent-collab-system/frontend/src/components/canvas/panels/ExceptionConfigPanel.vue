<template>
  <div class="space-y-4 rounded-[26px] border border-slate-300/90 bg-[linear-gradient(180deg,#fbfbfb_0%,#f4f4f5_100%)] p-5 shadow-[0_18px_45px_rgba(113,113,122,0.10)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-slate-600/80">异常节点</div>
        <div class="mt-1 text-base font-semibold text-slate-900">异常策略与兜底节点</div>
      </div>
      <span class="rounded-full border border-slate-300 bg-white px-3 py-1 text-[11px] font-medium text-slate-700">exception</span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-slate-200/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">异常处理</div>
      <div class="grid gap-3 md:grid-cols-2">
        <el-input v-model="exceptionPolicy" placeholder="异常策略，如 continue / stop / fallback" />
        <el-input v-model="fallbackNode" placeholder="兜底节点 ID / 名称" />
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-slate-200/60 space-y-3">
      <div class="text-xs uppercase tracking-[0.22em] text-slate-500">通知目标</div>
      <el-input v-model="notifyTarget" placeholder="通知目标，如 monitor.workbench / chat.alert" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ExceptionNodeConfig } from '@/types/workflow'

const props = defineProps<{ modelValue: Record<string, unknown> }>()
const emit = defineEmits<{ 'update:modelValue': [value: ExceptionNodeConfig] }>()

const currentConfig = computed<ExceptionNodeConfig>(() => {
  const config = props.modelValue as ExceptionNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    exceptionPolicy: config.exceptionPolicy ?? '',
    fallbackNode: config.fallbackNode ?? '',
    notifyTarget: config.notifyTarget ?? '',
  }
})

const updateConfig = (patch: Partial<ExceptionNodeConfig>) => emit('update:modelValue', { ...currentConfig.value, ...patch })
const exceptionPolicy = computed({ get: () => currentConfig.value.exceptionPolicy ?? '', set: (value: string) => updateConfig({ exceptionPolicy: value }) })
const fallbackNode = computed({ get: () => currentConfig.value.fallbackNode ?? '', set: (value: string) => updateConfig({ fallbackNode: value }) })
const notifyTarget = computed({ get: () => currentConfig.value.notifyTarget ?? '', set: (value: string) => updateConfig({ notifyTarget: value }) })
</script>
