<template>
  <div class="space-y-4 rounded-[26px] border border-sky-200/80 bg-[linear-gradient(180deg,#f8fbff_0%,#f1f6ff_100%)] p-5 shadow-[0_18px_45px_rgba(59,130,246,0.10)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-sky-600/80">条件节点</div>
        <div class="mt-1 text-base font-semibold text-slate-900">条件表达式与路径分流</div>
      </div>
      <span class="rounded-full border border-sky-300 bg-white px-3 py-1 text-[11px] font-medium text-sky-700">condition</span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-sky-100/60 space-y-3">
      <div class="text-xs uppercase tracking-[0.22em] text-slate-500">判断规则</div>
      <el-input v-model="expression" placeholder="条件表达式，如 stock_count < safety_limit" />
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-sky-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">路径标签</div>
      <div class="grid gap-3 md:grid-cols-2">
        <el-input v-model="trueLabel" placeholder="满足条件时路径标签" />
        <el-input v-model="falseLabel" placeholder="不满足条件时路径标签" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ConditionNodeConfig } from '@/types/workflow'

const props = defineProps<{ modelValue: Record<string, unknown> }>()
const emit = defineEmits<{ 'update:modelValue': [value: ConditionNodeConfig] }>()

const currentConfig = computed<ConditionNodeConfig>(() => {
  const config = props.modelValue as ConditionNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    expression: config.expression ?? '',
    trueLabel: config.trueLabel ?? '',
    falseLabel: config.falseLabel ?? '',
  }
})

const updateConfig = (patch: Partial<ConditionNodeConfig>) => emit('update:modelValue', { ...currentConfig.value, ...patch })
const expression = computed({ get: () => currentConfig.value.expression ?? '', set: (value: string) => updateConfig({ expression: value }) })
const trueLabel = computed({ get: () => currentConfig.value.trueLabel ?? '', set: (value: string) => updateConfig({ trueLabel: value }) })
const falseLabel = computed({ get: () => currentConfig.value.falseLabel ?? '', set: (value: string) => updateConfig({ falseLabel: value }) })
</script>
