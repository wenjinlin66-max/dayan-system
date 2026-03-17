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
        <div class="grid gap-3 md:grid-cols-2">
          <el-input v-if="decisionMode === 'rule'" v-model="ruleSetRef" placeholder="规则集编码，如 inventory_replenishment_rules" />
          <el-select v-if="decisionMode === 'model'" v-model="modelType" placeholder="选择模型类型">
            <el-option v-for="item in modelTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-input v-if="decisionMode === 'model'" v-model="optimizationGoal" placeholder="优化目标，如 balance_cost_and_efficiency" />
          <el-input v-if="decisionMode === 'llm'" v-model="promptTemplate" placeholder="提示模板，如 根据低库存事件生成可供 chat/table 执行的结构化风险方案" />
          <el-input v-if="decisionMode === 'llm'" v-model="outputTemplate" placeholder="输出模板，如 decision.result.execution_bundle.v1" />
        </div>
      </div>
    </section>

    <section v-if="decisionMode === 'rule'" class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-emerald-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">规则型设计</div>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">严重度阈值</div>
          <el-input v-model="severityThresholdsText" type="textarea" :rows="6" placeholder="high=0.3&#10;medium=0.8&#10;low=1.0" />
          <div class="text-xs leading-5 text-slate-400">仅接受 key=value 数字配置；非法值会被自动忽略。</div>
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">推荐动作模板</div>
          <el-input v-model="actionType" placeholder="动作类型，如 create_department_table_record" />
          <el-input v-model="severityField" placeholder="严重度字段，如 severity" />
          <el-input v-model="targetItemField" placeholder="目标物料字段，如 item_id" />
          <el-input v-model="quantityField" placeholder="建议数量字段，如 recommended_quantity" />
        </div>
      </div>
    </section>

    <section v-if="decisionMode === 'model'" class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-emerald-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">模型型设计</div>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">模型标识</div>
          <el-input v-model="modelRef" placeholder="模型引用，如 replenishment.optimizer.v1" />
          <el-input v-model="candidateActionsText" type="textarea" :rows="4" placeholder="append_row&#10;request_approval&#10;notify_manager" />
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">目标权重</div>
          <el-input v-model="objectiveWeightsText" type="textarea" :rows="4" placeholder="cost=0.35&#10;timeliness=0.40&#10;stability=0.25" />
          <el-input v-model="capacityLimitsText" type="textarea" :rows="4" placeholder="max_quantity=500&#10;min_quantity=20" />
          <div class="text-xs leading-5 text-slate-400">目标权重与容量上下限仅接受数字；非法值不会写入配置。</div>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-emerald-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">约束与知识</div>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">约束列表</div>
          <el-input v-model="constraintsText" type="textarea" :rows="5" placeholder="库存不可低于 0&#10;优先保障关键物料&#10;输出必须稳定包含 chat_report 与 table_write" />
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">知识范围</div>
          <el-input v-model="ragRefsText" type="textarea" :rows="5" placeholder="inventory&#10;policy.replenishment" />
        </div>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-2">
        <el-switch v-model="includeExplanation" inline-prompt active-text="解释" inactive-text="解释" />
        <el-switch v-model="includeCitations" inline-prompt active-text="引用" inactive-text="引用" />
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

const modelTypeOptions = [
  { label: '评分卡', value: 'scorecard' },
  { label: '产能规划', value: 'capacity_planner' },
  { label: '风险均衡', value: 'risk_balancer' },
]

const currentConfig = computed<DecisionNodeConfig>(() => {
  const config = props.modelValue as DecisionNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    decision_mode: config.decision_mode ?? 'rule',
    rule_set_ref: config.rule_set_ref ?? '',
    rule_config: typeof config.rule_config === 'object' && config.rule_config ? config.rule_config : {},
    model_type: config.model_type ?? 'scorecard',
    model_ref: config.model_ref ?? '',
    model_params: typeof config.model_params === 'object' && config.model_params ? config.model_params : {},
    optimization_goal: config.optimization_goal ?? '',
    constraints: config.constraints ?? [],
    prompt_template: config.prompt_template ?? '',
    output_template: config.output_template ?? '',
    include_explanation: config.include_explanation ?? true,
    include_citations: config.include_citations ?? true,
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

const outputTemplate = computed({
  get: () => currentConfig.value.output_template ?? '',
  set: (value: string) => updateConfig({ output_template: value }),
})

const modelType = computed({
  get: () => currentConfig.value.model_type ?? 'scorecard',
  set: (value: DecisionNodeConfig['model_type']) => updateConfig({ model_type: value }),
})

const modelRef = computed({
  get: () => currentConfig.value.model_ref ?? '',
  set: (value: string) => updateConfig({ model_ref: value }),
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

const ruleConfig = computed<Record<string, unknown>>(() => (currentConfig.value.rule_config ?? {}) as Record<string, unknown>)
const modelParams = computed<Record<string, unknown>>(() => (currentConfig.value.model_params ?? {}) as Record<string, unknown>)

const severityThresholdsText = computed({
  get: () => Object.entries((ruleConfig.value.severity_thresholds as Record<string, unknown>) ?? {}).map(([key, value]) => `${key}=${String(value)}`).join('\n'),
  set: (value: string) => {
    const severityThresholds = parseNumericMap(value)
    updateConfig({
      rule_config: {
        ...ruleConfig.value,
        severity_thresholds: severityThresholds,
      },
    })
  },
})

const severityField = computed({
  get: () => String(ruleConfig.value.severity_field ?? ''),
  set: (value: string) => updateConfig({ rule_config: { ...ruleConfig.value, severity_field: value } }),
})

const targetItemField = computed({
  get: () => String(ruleConfig.value.target_item_field ?? ''),
  set: (value: string) => updateConfig({ rule_config: { ...ruleConfig.value, target_item_field: value } }),
})

const quantityField = computed({
  get: () => String(ruleConfig.value.quantity_field ?? ''),
  set: (value: string) => updateConfig({ rule_config: { ...ruleConfig.value, quantity_field: value } }),
})

const actionType = computed({
  get: () => String(ruleConfig.value.action_type ?? ''),
  set: (value: string) => updateConfig({ rule_config: { ...ruleConfig.value, action_type: value } }),
})

const candidateActionsText = computed({
  get: () => ((modelParams.value.candidate_actions as string[]) ?? []).join('\n'),
  set: (value: string) => updateConfig({
    model_params: {
      ...modelParams.value,
      candidate_actions: value.split('\n').map((item) => item.trim()).filter(Boolean),
    },
  }),
})

const objectiveWeightsText = computed({
  get: () => Object.entries((modelParams.value.objective_weights as Record<string, unknown>) ?? {}).map(([key, value]) => `${key}=${String(value)}`).join('\n'),
  set: (value: string) => {
    const objectiveWeights = parseNumericMap(value)
    updateConfig({
      model_params: {
        ...modelParams.value,
        objective_weights: objectiveWeights,
      },
    })
  },
})

const capacityLimitsText = computed({
  get: () => Object.entries((modelParams.value.capacity_limits as Record<string, unknown>) ?? {}).map(([key, value]) => `${key}=${String(value)}`).join('\n'),
  set: (value: string) => {
    const capacityLimits = parseNumericMap(value)
    updateConfig({
      model_params: {
        ...modelParams.value,
        capacity_limits: capacityLimits,
      },
    })
  },
})

const includeExplanation = computed({
  get: () => currentConfig.value.include_explanation ?? true,
  set: (value: boolean) => updateConfig({ include_explanation: value }),
})

const includeCitations = computed({
  get: () => currentConfig.value.include_citations ?? true,
  set: (value: boolean) => updateConfig({ include_citations: value }),
})

const parseNumericMap = (value: string): Record<string, number> => {
  const entries = value.split('\n').map((item) => item.trim()).filter(Boolean)
  return Object.fromEntries(entries.flatMap((item) => {
    const [key, rawValue = ''] = item.split('=')
    const parsedKey = key.trim()
    const parsedValue = Number(rawValue.trim())
    if (!parsedKey || !Number.isFinite(parsedValue)) {
      return []
    }
    return [[parsedKey, parsedValue]]
  }))
}
</script>
