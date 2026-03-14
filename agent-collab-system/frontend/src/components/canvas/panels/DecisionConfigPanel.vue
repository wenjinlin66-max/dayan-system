<template>
  <div class="space-y-4 rounded-[26px] border border-emerald-200/80 bg-[linear-gradient(180deg,#f7fff9_0%,#ecfff5_100%)] p-5 shadow-[0_18px_45px_rgba(16,185,129,0.10)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-emerald-600/80">决策智能体</div>
        <div class="mt-1 text-base font-semibold text-slate-900">规则 / 模型 / 智能推理</div>
        <div class="mt-1 text-sm leading-6 text-slate-500">统一整理决策模式、规则集、优化目标与知识引用，避免参数散乱堆叠。</div>
      </div>
      <span class="rounded-full border border-emerald-300 bg-white px-3 py-1 text-[11px] font-medium text-emerald-700">decision_agent</span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-emerald-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">决策模式</div>
      <div class="space-y-3">
        <el-segmented v-model="decisionMode" :options="modeOptions" block />
        <el-input v-if="decisionMode === 'rule'" v-model="ruleSetRef" placeholder="规则集编码，如 inventory_replenishment_rules" />
        <el-input v-if="decisionMode === 'model'" v-model="optimizationGoal" placeholder="优化目标，如 balance_cost_and_efficiency" />
        <el-input v-if="decisionMode === 'llm'" v-model="promptTemplate" placeholder="提示模板，如 根据低库存事件生成补货建议" />
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-emerald-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">约束与知识</div>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">约束列表</div>
          <el-input v-model="constraintsText" type="textarea" :rows="5" placeholder="库存不可低于 0&#10;优先保障关键物料" />
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">知识范围</div>
          <el-input v-model="ragRefsText" type="textarea" :rows="5" placeholder="inventory&#10;policy.replenishment" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { DecisionNodeConfig } from '@/types/workflow'

const props = defineProps<{ modelValue: Record<string, unknown> }>()
const emit = defineEmits<{ 'update:modelValue': [value: DecisionNodeConfig] }>()

const modeOptions = [
  { label: '规则型', value: 'rule' },
  { label: '模型型', value: 'model' },
  { label: '智能型', value: 'llm' },
]

const currentConfig = computed<DecisionNodeConfig>(() => {
  const config = props.modelValue as DecisionNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    decision_mode: config.decision_mode ?? 'rule',
    rule_set_ref: config.rule_set_ref ?? '',
    optimization_goal: config.optimization_goal ?? '',
    constraints: config.constraints ?? [],
    prompt_template: config.prompt_template ?? '',
    rag_refs: config.rag_refs ?? [],
  }
})

const updateConfig = (patch: Partial<DecisionNodeConfig>) => {
  emit('update:modelValue', {
    ...currentConfig.value,
    ...patch,
  })
}

const decisionMode = computed({
  get: () => currentConfig.value.decision_mode ?? 'rule',
  set: (value: DecisionNodeConfig['decision_mode']) => updateConfig({ decision_mode: value }),
})

const ruleSetRef = computed({
  get: () => currentConfig.value.rule_set_ref ?? '',
  set: (value: string) => updateConfig({ rule_set_ref: value }),
})

const optimizationGoal = computed({
  get: () => currentConfig.value.optimization_goal ?? '',
  set: (value: string) => updateConfig({ optimization_goal: value }),
})

const promptTemplate = computed({
  get: () => currentConfig.value.prompt_template ?? '',
  set: (value: string) => updateConfig({ prompt_template: value }),
})

const constraintsText = computed({
  get: () => (currentConfig.value.constraints ?? []).join('\n'),
  set: (value: string) => {
    updateConfig({
      constraints: value.split('\n').map((item) => item.trim()).filter(Boolean),
    })
  },
})

const ragRefsText = computed({
  get: () => (currentConfig.value.rag_refs ?? []).join('\n'),
  set: (value: string) => {
    updateConfig({
      rag_refs: value.split('\n').map((item) => item.trim()).filter(Boolean),
    })
  },
})
</script>
