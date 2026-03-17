<template>
  <div class="space-y-4 rounded-[26px] border border-amber-200/70 bg-[linear-gradient(180deg,#fffaf2_0%,#fff4e8_100%)] p-5 shadow-[0_18px_45px_rgba(245,158,11,0.12)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-amber-600/80">执行智能体</div>
        <div class="mt-1 text-base font-semibold text-slate-900">单目标执行器 + 审批编排</div>
        <div class="mt-1 text-sm leading-6 text-slate-500">一个 execution_agent 负责一个执行目标；若既要发对话框又要改业务表，请在决策节点后接 parallel，再并列挂多个执行智能体。</div>
      </div>
      <span class="rounded-full border border-amber-300 bg-white px-3 py-1 text-[11px] font-medium text-amber-700">
        peer-target execution
      </span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-amber-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">执行策略</div>
      <div class="grid gap-4 xl:grid-cols-3">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">目标选择方式</div>
          <el-segmented v-model="executionTargetMode" :options="targetModeOptions" block />
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">执行目标类型</div>
          <el-segmented v-model="targetType" :options="targetTypeOptions" block />
        </div>
        <div class="rounded-2xl border border-slate-200 bg-slate-50/90 p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-sm font-medium text-slate-700">进入对话审批</div>
              <div class="mt-1 text-xs leading-5 text-slate-500">高风险执行先挂起，把审批卡片送到部门对话区的审批工作区；审批通过后继续执行当前 execution_agent。</div>
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
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">目标配置</div>

      <template v-if="targetType === 'department_chat'">
        <div class="rounded-2xl border border-emerald-200 bg-emerald-50/80 px-3 py-2 text-xs leading-5 text-emerald-800">
          当前 execution_agent 负责“把决策结果发送到部门对话框”。报告正文优先采用你在决策型节点中产出的结构化内容，再按下方模板组织文本。
        </div>
        <div class="mt-3 grid gap-3 md:grid-cols-2">
          <el-input v-model="targetRef" placeholder="对话框目标编码，可留空自动生成 department_chat.<dept_id>" />
          <el-select v-model="deptRouteMode" placeholder="对话框路由方式">
            <el-option label="当前执行部门" value="current_dept" />
            <el-option label="固定部门" value="fixed_dept" />
            <el-option label="从决策结果推导" value="derived" />
          </el-select>
          <el-select v-if="deptRouteMode === 'fixed_dept'" v-model="fixedDeptId" placeholder="固定目标部门">
            <el-option v-for="item in targetDeptOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="resultTargetDeptId" placeholder="对话框结果部门（默认跟随目标路由）">
            <el-option label="自动跟随目标部门" value="" />
            <el-option v-for="item in targetDeptOptions" :key="`chat-${item.value}`" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="mt-3 grid gap-3 md:grid-cols-2">
          <div class="rounded-2xl border border-slate-200 bg-slate-50/90 p-3">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-sm font-medium text-slate-700">发送摘要</div>
                <div class="mt-1 text-xs leading-5 text-slate-500">将决策摘要作为报告首段。</div>
              </div>
              <el-switch v-model="chatSendSummary" />
            </div>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50/90 p-3">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-sm font-medium text-slate-700">失败原因回传</div>
                <div class="mt-1 text-xs leading-5 text-slate-500">为执行失败后的报告保留字段位。</div>
              </div>
              <el-switch v-model="chatSendFailureReason" />
            </div>
          </div>
        </div>
        <div class="mt-3">
          <div class="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">对话框报告模板</div>
          <el-input
            v-model="resultTemplate"
            type="textarea"
            :rows="7"
            placeholder="支持 {{decision_summary}}、{{risk_level}}、{{decision_explanation}}、{{recommended_actions}}、{{chat_report_title}}、{{chat_report_content}}、{{chat_report_audience}}、{{target_item_id}}、{{recommended_quantity}}、{{result_summary}} 等变量。"
          />
        </div>
      </template>

      <template v-else-if="targetType === 'department_table'">
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
            <el-option label="从决策结果推导" value="derived" />
          </el-select>
          <el-select v-if="deptRouteMode === 'fixed_dept'" v-model="fixedDeptId" placeholder="固定目标部门">
            <el-option v-for="item in targetDeptOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="mt-3">
          <el-input v-model="idempotencyKeyTemplate" placeholder="幂等键模板，如 {{dept_id}}:{{execution_id}}:{{node_id}}" />
        </div>
        <div class="mt-3 grid gap-4 lg:grid-cols-2">
          <div class="space-y-2">
            <div class="text-sm font-medium text-slate-700">字段映射</div>
            <el-input
              v-model="rowMappingText"
              type="textarea"
              :rows="6"
              placeholder="物料编码=decision_payload.table_write.item_id&#10;建议补货量=decision_payload.table_write.recommended_quantity"
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
        <div class="mt-4 rounded-2xl border border-slate-200 bg-slate-50/90 p-4">
          <div class="mb-2 text-sm font-medium text-slate-700">执行结果通知（可选）</div>
          <div class="text-xs leading-5 text-slate-500">如果你既要“改业务表”又要“发正式风险报告到对话框”，推荐在 parallel 后再挂一个单独的 department_chat 执行节点；这里只保留执行结果摘要通知作为辅助能力。</div>
          <div class="mt-3 grid gap-3 md:grid-cols-2">
            <el-segmented v-model="resultDelivery" :options="resultDeliveryOptions" block />
            <el-select v-if="resultDelivery === 'chat'" v-model="resultTargetDeptId" placeholder="结果通知部门">
              <el-option label="自动推导（否则回退当前执行部门）" value="" />
              <el-option v-for="item in targetDeptOptions" :key="`result-${item.value}`" :label="item.label" :value="item.value" />
            </el-select>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="rounded-2xl border border-indigo-200 bg-indigo-50/80 px-3 py-2 text-xs leading-5 text-indigo-800">
          这些第三方执行目标已经被纳入与业务表格、对话框同级的目标体系；当前前端先支持配置入口，后端运行时仍以 department_chat / department_table 为主，后续再继续接 Feishu / Email / MCP 真实 executor。
        </div>
        <div class="mt-3 grid gap-3 md:grid-cols-2">
          <el-input v-model="targetRef" placeholder="目标编码，如 feishu.bot.risk_notice" />
          <el-input v-model="provider" placeholder="provider，如 feishu / smtp / mcp" />
          <el-input v-model="operation" placeholder="动作，如 send_message / send_mail / call_tool" />
          <el-select v-model="deptRouteMode" placeholder="部门路由方式">
            <el-option label="当前执行部门" value="current_dept" />
            <el-option label="固定部门" value="fixed_dept" />
            <el-option label="从决策结果推导" value="derived" />
          </el-select>
          <el-select v-if="deptRouteMode === 'fixed_dept'" v-model="fixedDeptId" placeholder="固定目标部门">
            <el-option v-for="item in targetDeptOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { ExecutionNodeConfig, ExecutionTargetConfig, ExecutionTargetTypeV2 } from '@/types/workflow'
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

const targetTypeOptions = [
  { label: '对话框报告', value: 'department_chat' },
  { label: '业务表格', value: 'department_table' },
  { label: '飞书', value: 'feishu' },
  { label: '邮箱', value: 'email' },
  { label: 'MCP', value: 'mcp' },
]

const approvalModeOptions = [
  { label: '按风险', value: 'risk_based' },
  { label: '总是审批', value: 'always' },
  { label: '直接执行', value: 'never' },
]

const resultDeliveryOptions = [
  { label: '不通知', value: 'none' },
  { label: '对话区', value: 'chat' },
  { label: '事件流', value: 'event' },
  { label: '监控台', value: 'monitor' },
]

const targetDeptOptions = ERP_DEPARTMENT_OPTIONS.filter((item) => item.value !== 'ceo')

const createDefaultTarget = (targetType: ExecutionTargetTypeV2): ExecutionTargetConfig => {
  if (targetType === 'department_chat') {
    return {
      target_type: 'department_chat',
      target_ref: '',
      provider: 'chat',
      operation: 'send_report',
      dept_route_mode: 'current_dept',
      fixed_dept_id: '',
    }
  }
  if (targetType === 'department_table') {
    return {
      target_type: 'department_table',
      target_ref: '',
      provider: 'bitable',
      operation: 'append_row',
      dept_route_mode: 'current_dept',
      fixed_dept_id: '',
      idempotency_key_template: '{{dept_id}}:{{execution_id}}:{{node_id}}',
      row_mapping: {},
      default_values: {},
    }
  }
  return {
    target_type: targetType,
    target_ref: '',
    provider: targetType,
    operation: '',
    dept_route_mode: 'current_dept',
    fixed_dept_id: '',
  }
}

const normalizePrimaryTarget = (config: ExecutionNodeConfig): ExecutionTargetConfig => {
  const current = config.execution_targets?.[0] as ExecutionTargetConfig | undefined
  if (current && typeof current.target_type === 'string') {
    return current
  }
  if (config.result_delivery === 'chat') {
    return createDefaultTarget('department_chat')
  }
  return createDefaultTarget('department_table')
}

const currentConfig = computed<ExecutionNodeConfig>(() => {
  const config = props.modelValue as ExecutionNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    execution_target_mode: config.execution_target_mode ?? 'manual',
    approval_mode: config.approval_mode ?? 'risk_based',
    approval_required: config.approval_required ?? true,
    result_delivery: config.result_delivery ?? 'none',
    result_target_dept_id: typeof config.result_target_dept_id === 'string' ? config.result_target_dept_id : '',
    chat_delivery: {
      send_summary: config.chat_delivery?.send_summary ?? true,
      send_failure_reason: config.chat_delivery?.send_failure_reason ?? true,
    },
    result_template: typeof config.result_template === 'string' ? config.result_template : '',
    failure_delivery: config.failure_delivery ?? 'none',
    execution_targets: [normalizePrimaryTarget(config)],
  }
})

const updateConfig = (patch: Partial<ExecutionNodeConfig>) => {
  emit('update:modelValue', {
    ...currentConfig.value,
    ...patch,
  })
}

const primaryTarget = computed(() => currentConfig.value.execution_targets?.[0] ?? createDefaultTarget('department_chat'))

const updateTarget = (patch: Partial<ExecutionTargetConfig>) => {
  updateConfig({
    execution_targets: [
      {
        ...primaryTarget.value,
        ...patch,
      } as ExecutionTargetConfig,
    ],
  })
}

const executionTargetMode = computed({
  get: () => currentConfig.value.execution_target_mode ?? 'manual',
  set: (value: ExecutionNodeConfig['execution_target_mode']) => updateConfig({ execution_target_mode: value }),
})

const targetType = computed<ExecutionTargetTypeV2>({
  get: () => (primaryTarget.value.target_type as ExecutionTargetTypeV2) ?? 'department_chat',
  set: (value) => {
    updateConfig({
      execution_targets: [createDefaultTarget(value)],
      result_delivery: value === 'department_chat' ? 'none' : currentConfig.value.result_delivery ?? 'none',
    })
  },
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
  get: () => currentConfig.value.result_delivery ?? 'none',
  set: (value: ExecutionNodeConfig['result_delivery']) => updateConfig({ result_delivery: value }),
})

const targetRef = computed({
  get: () => primaryTarget.value.target_ref ?? '',
  set: (value: string) => updateTarget({ target_ref: value }),
})

const provider = computed({
  get: () => primaryTarget.value.provider ?? '',
  set: (value: string) => updateTarget({ provider: value }),
})

const operation = computed({
  get: () => primaryTarget.value.operation ?? '',
  set: (value: string) => updateTarget({ operation: value }),
})

const deptRouteMode = computed({
  get: () => primaryTarget.value.dept_route_mode ?? 'current_dept',
  set: (value: string) => updateTarget({ dept_route_mode: value as ExecutionTargetConfig['dept_route_mode'] }),
})

const fixedDeptId = computed({
  get: () => primaryTarget.value.fixed_dept_id ?? '',
  set: (value: string) => updateTarget({ fixed_dept_id: value }),
})

const idempotencyKeyTemplate = computed({
  get: () => ('idempotency_key_template' in primaryTarget.value ? primaryTarget.value.idempotency_key_template : '') ?? '{{dept_id}}:{{execution_id}}:{{node_id}}',
  set: (value: string) => updateTarget({ idempotency_key_template: value } as Partial<ExecutionTargetConfig>),
})

const resultTargetDeptId = computed({
  get: () => currentConfig.value.result_target_dept_id ?? '',
  set: (value: string) => updateConfig({ result_target_dept_id: value || undefined }),
})

const chatSendSummary = computed({
  get: () => currentConfig.value.chat_delivery?.send_summary ?? true,
  set: (value: boolean) => updateConfig({ chat_delivery: { ...(currentConfig.value.chat_delivery ?? {}), send_summary: value } }),
})

const chatSendFailureReason = computed({
  get: () => currentConfig.value.chat_delivery?.send_failure_reason ?? true,
  set: (value: boolean) => updateConfig({ chat_delivery: { ...(currentConfig.value.chat_delivery ?? {}), send_failure_reason: value } }),
})

const resultTemplate = computed({
  get: () => currentConfig.value.result_template ?? '',
  set: (value: string) => updateConfig({ result_template: value }),
})

const encodeMappingText = (value?: Record<string, string>) =>
  Object.entries(value ?? {})
    .map(([key, path]) => `${key}=${path}`)
    .join('\n')

const parseMappingText = (value: string) =>
  value
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

const rowMappingText = computed({
  get: () => encodeMappingText(('row_mapping' in primaryTarget.value ? primaryTarget.value.row_mapping : undefined) as Record<string, string> | undefined),
  set: (value: string) => updateTarget({ row_mapping: parseMappingText(value) } as Partial<ExecutionTargetConfig>),
})

const defaultValuesText = computed({
  get: () => encodeMappingText(('default_values' in primaryTarget.value ? primaryTarget.value.default_values : undefined) as Record<string, string> | undefined),
  set: (value: string) => updateTarget({ default_values: parseMappingText(value) } as Partial<ExecutionTargetConfig>),
})
</script>
