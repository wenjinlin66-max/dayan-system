<template>
  <div class="space-y-4 rounded-[26px] border border-amber-200/70 bg-[linear-gradient(180deg,#fffaf2_0%,#fff4e8_100%)] p-5 shadow-[0_18px_45px_rgba(245,158,11,0.12)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-amber-600/80">执行智能体</div>
        <div class="mt-1 text-base font-semibold text-slate-900">执行目标与审批编排</div>
        <div class="mt-1 text-sm leading-6 text-slate-500">聚焦目标注册、审批策略、部门路由和写入映射，让界面更利于快速扫描。</div>
      </div>
      <span class="rounded-full border border-amber-300 bg-white px-3 py-1 text-[11px] font-medium text-amber-700">
        department_table
      </span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-amber-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">执行策略</div>
      <div class="grid gap-4 lg:grid-cols-3">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">目标模式</div>
          <el-segmented v-model="executionTargetMode" :options="targetModeOptions" block />
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">结果回传</div>
          <el-segmented v-model="resultDelivery" :options="resultDeliveryOptions" block />
        </div>
        <div class="rounded-2xl border border-slate-200 bg-slate-50/90 p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-sm font-medium text-slate-700">进入对话审批</div>
              <div class="mt-1 text-xs leading-5 text-slate-500">在执行前先投递审批卡片，适合高风险写入动作。</div>
            </div>
            <el-switch v-model="approvalRequired" />
          </div>
          <div class="mt-3">
            <div class="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">审批模式</div>
            <el-segmented v-model="approvalMode" :options="approvalModeOptions" block />
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-amber-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">目标注册与路由</div>
      <div class="grid gap-3 md:grid-cols-2">
        <el-input v-model="targetRef" placeholder="目标编码，如 dept_table.production.replenishment_register" />
        <el-select v-model="provider" placeholder="底层 provider">
          <el-option label="飞书多维表格 / bitable" value="bitable" />
          <el-option label="通用 spreadsheet" value="spreadsheet" />
          <el-option label="自定义表格服务" value="custom_table" />
        </el-select>
        <el-select v-model="operation" placeholder="写入动作">
          <el-option label="新增一行 append_row" value="append_row" />
          <el-option label="更新或新增 upsert_row" value="upsert_row" />
          <el-option label="更新已有记录 update_row" value="update_row" />
        </el-select>
        <el-select v-model="deptRouteMode" placeholder="部门路由方式">
          <el-option label="当前执行部门" value="current_dept" />
          <el-option label="固定部门" value="fixed_dept" />
          <el-option label="从上下文推导" value="derived" />
        </el-select>
        <el-select v-if="deptRouteMode === 'fixed_dept'" v-model="fixedDeptId" placeholder="固定目标部门">
          <el-option v-for="item in targetDeptOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>
      <div class="mt-3">
        <el-input v-model="idempotencyKeyTemplate" placeholder="幂等键模板，如 {{dept_id}}:{{execution_id}}:{{node_id}}" />
      </div>
      <div v-if="resultDelivery === 'chat'" class="mt-3">
        <div class="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">结果回传部门</div>
        <el-select v-model="resultTargetDeptId" class="w-full" placeholder="默认当前执行部门对话框">
          <el-option label="当前执行部门对话框" value="" />
          <el-option v-for="item in targetDeptOptions" :key="`result-${item.value}`" :label="item.label" :value="item.value" />
        </el-select>
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-amber-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">写入内容映射</div>
      <div class="grid gap-4 lg:grid-cols-2">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">字段映射</div>
          <el-input
            v-model="rowMappingText"
            type="textarea"
            :rows="6"
            placeholder="物料编码=decision_payload.target_item_id&#10;建议补货量=decision_payload.recommended_quantity"
          />
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">缺省值</div>
          <el-input
            v-model="defaultValuesText"
            type="textarea"
            :rows="6"
            placeholder="状态=待处理&#10;来源=对话执行"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { ExecutionNodeConfig } from '@/types/workflow'
import { ERP_DEPARTMENT_OPTIONS } from '@/utils/erpDepartments'

const props = defineProps<{
  modelValue: Record<string, unknown>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ExecutionNodeConfig]
}>()

const targetModeOptions = [
  { label: '手动目标', value: 'manual' },
  { label: 'AI 选择', value: 'ai_select' },
]

const approvalModeOptions = [
  { label: '按风险', value: 'risk_based' },
  { label: '总是审批', value: 'always' },
  { label: '直接执行', value: 'never' },
]

const resultDeliveryOptions = [
  { label: '对话区', value: 'chat' },
  { label: '事件流', value: 'event' },
  { label: '监控台', value: 'monitor' },
]

const targetDeptOptions = ERP_DEPARTMENT_OPTIONS.filter((item) => item.value !== 'ceo')

const currentConfig = computed<ExecutionNodeConfig>(() => {
  const config = props.modelValue as ExecutionNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    execution_target_mode: config.execution_target_mode ?? 'manual',
    approval_mode: config.approval_mode ?? 'risk_based',
    approval_required: config.approval_required ?? true,
    result_delivery: config.result_delivery ?? 'chat',
    result_target_dept_id: typeof config.result_target_dept_id === 'string' ? config.result_target_dept_id : '',
    execution_targets:
      config.execution_targets?.length
        ? config.execution_targets
        : [
            {
              target_type: 'department_table',
              target_ref: '',
              provider: 'bitable',
              operation: 'append_row',
              dept_route_mode: 'current_dept',
              fixed_dept_id: '',
              idempotency_key_template: '{{dept_id}}:{{execution_id}}:{{node_id}}',
              row_mapping: {},
              default_values: {},
            },
          ],
  }
})

const updateConfig = (patch: Partial<ExecutionNodeConfig>) => {
  const nextConfig: ExecutionNodeConfig = {
    ...currentConfig.value,
    ...patch,
  }
  emit('update:modelValue', nextConfig)
}

const primaryTarget = computed(() => currentConfig.value.execution_targets?.[0])

const executionTargetMode = computed({
  get: () => currentConfig.value.execution_target_mode ?? 'manual',
  set: (value: ExecutionNodeConfig['execution_target_mode']) => updateConfig({ execution_target_mode: value }),
})

const approvalMode = computed({
  get: () => currentConfig.value.approval_mode ?? 'risk_based',
  set: (value: ExecutionNodeConfig['approval_mode']) => updateConfig({ approval_mode: value }),
})

const approvalRequired = computed({
  get: () => currentConfig.value.approval_required ?? true,
  set: (value: boolean) => updateConfig({ approval_required: value }),
})

const resultDelivery = computed({
  get: () => currentConfig.value.result_delivery ?? 'chat',
  set: (value: ExecutionNodeConfig['result_delivery']) => updateConfig({ result_delivery: value }),
})

const updateTarget = (patch: Record<string, unknown>) => {
  const existing = primaryTarget.value ?? {
    target_type: 'department_table',
    target_ref: '',
    provider: 'bitable',
    operation: 'append_row',
    dept_route_mode: 'current_dept',
    fixed_dept_id: '',
  }
  updateConfig({
    execution_targets: [
      {
        ...existing,
        ...patch,
        target_type: 'department_table',
      },
    ],
  })
}

const targetRef = computed({
  get: () => primaryTarget.value?.target_ref ?? '',
  set: (value: string) => updateTarget({ target_ref: value }),
})

const provider = computed({
  get: () => primaryTarget.value?.provider ?? 'bitable',
  set: (value: string) => updateTarget({ provider: value }),
})

const operation = computed({
  get: () => primaryTarget.value?.operation ?? 'append_row',
  set: (value: string) => updateTarget({ operation: value }),
})

const deptRouteMode = computed({
  get: () => primaryTarget.value?.dept_route_mode ?? 'current_dept',
  set: (value: string) => updateTarget({ dept_route_mode: value }),
})

const idempotencyKeyTemplate = computed({
  get: () => primaryTarget.value?.idempotency_key_template ?? '{{dept_id}}:{{execution_id}}:{{node_id}}',
  set: (value: string) => updateTarget({ idempotency_key_template: value }),
})

const fixedDeptId = computed({
  get: () => primaryTarget.value?.fixed_dept_id ?? '',
  set: (value: string) => updateTarget({ fixed_dept_id: value }),
})

const resultTargetDeptId = computed({
  get: () => currentConfig.value.result_target_dept_id ?? '',
  set: (value: string) => updateConfig({ result_target_dept_id: value || undefined }),
})

const encodeMappingText = (value?: Record<string, string>) =>
  Object.entries(value ?? {})
    .map(([key, path]) => `${key}=${path}`)
    .join('\n')

const parseMappingText = (value: string) => {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((accumulator, line) => {
      const [key, ...rest] = line.split('=')
      if (!key || rest.length === 0) {
        return accumulator
      }
      accumulator[key.trim()] = rest.join('=').trim()
      return accumulator
    }, {})
}

const rowMappingText = computed({
  get: () => encodeMappingText(primaryTarget.value?.row_mapping as Record<string, string> | undefined),
  set: (value: string) => updateTarget({ row_mapping: parseMappingText(value) }),
})

const defaultValuesText = computed({
  get: () => encodeMappingText(primaryTarget.value?.default_values as Record<string, string> | undefined),
  set: (value: string) => updateTarget({ default_values: parseMappingText(value) }),
})
</script>
