<template>
  <div class="space-y-4 rounded-[26px] border border-cyan-200/70 bg-[linear-gradient(180deg,#f7fdff_0%,#eef9ff_100%)] p-5 shadow-[0_18px_45px_rgba(14,165,233,0.10)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-cyan-600/80">感知智能体</div>
        <div class="mt-1 text-base font-semibold text-slate-900">事件感知与触发过滤</div>
        <div class="mt-1 text-sm leading-6 text-slate-500">来源、事件键、字段和触发规则都由后端元数据目录提供，配置员只做选择和调节，不再手写整段逻辑。</div>
      </div>
      <span class="rounded-full border border-cyan-300 bg-white px-3 py-1 text-[11px] font-medium text-cyan-700">sensor_agent</span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/90 p-4 shadow-sm shadow-cyan-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">来源定义</div>
      <div v-if="metadataLoading" class="rounded-2xl border border-dashed border-cyan-200 bg-cyan-50/70 px-4 py-5 text-sm text-cyan-700">
        正在从后端加载感知源目录...
      </div>
      <div v-else class="grid gap-3 md:grid-cols-2">
        <el-select v-model="sourceType" placeholder="选择来源类型">
          <el-option v-for="item in sourceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="sourceSystem" placeholder="选择来源系统" :disabled="availableSources.length === 0">
          <el-option v-for="item in availableSources" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="sourceTable" placeholder="选择来源表 / 数据域" :disabled="availableTables.length === 0">
          <el-option v-for="item in availableTables" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="sourceEventKey" placeholder="选择事件键" :disabled="availableEventKeys.length === 0">
          <el-option v-for="item in availableEventKeys" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/90 p-4 shadow-sm shadow-cyan-100/60">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">触发条件</div>
          <div class="mt-1 text-sm text-slate-500">每条规则都按字段、操作符和比较方式逐项配置，可按来源字段类型自动切换可用条件。</div>
        </div>
        <div class="flex items-center gap-3">
          <el-segmented v-model="conditionLogic" :options="logicOptions" />
          <el-button plain @click="addCondition">新增规则</el-button>
        </div>
      </div>

      <div v-if="conditionRows.length === 0" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-6 text-sm text-slate-500">
        还没有触发规则。可以先新增一条，例如“库存数量 小于 安全库存”。
      </div>

      <div v-else class="space-y-3">
        <div v-for="(condition, index) in conditionRows" :key="`${condition.field}-${index}`" class="rounded-2xl border border-slate-200 bg-slate-50/80 p-3">
          <div class="grid gap-3 xl:grid-cols-[minmax(0,1.1fr)_180px_150px_minmax(0,1fr)_auto]">
            <el-select :model-value="condition.field" placeholder="触发字段" @update:model-value="handleConditionFieldChange(index, $event)">
              <el-option v-for="field in availableFields" :key="field.value" :label="field.label" :value="field.value" />
            </el-select>

            <el-select :model-value="condition.operator" placeholder="操作符" @update:model-value="handleConditionOperatorChange(index, $event)">
              <el-option v-for="item in getOperatorOptions(condition.field)" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>

            <el-select :model-value="getCompareMode(condition)" placeholder="比较方式" @update:model-value="handleCompareModeChange(index, $event)">
              <el-option label="固定值" value="value" />
              <el-option label="字段对比" value="field" />
            </el-select>

            <template v-if="getCompareMode(condition) === 'field'">
              <el-select :model-value="condition.value_from_field" placeholder="选择对比字段" @update:model-value="handleConditionValueFieldChange(index, $event)">
                <el-option v-for="field in availableFields" :key="field.value" :label="field.label" :value="field.value" />
              </el-select>
            </template>

            <template v-else>
              <el-select
                v-if="getFieldMeta(condition.field)?.suggested_values?.length"
                :model-value="normalizeValue(condition.value)"
                placeholder="选择固定值"
                @update:model-value="handleConditionStaticValueChange(index, typeof $event === 'string' ? $event : String($event ?? ''))"
              >
                <el-option v-for="item in getFieldMeta(condition.field)?.suggested_values ?? []" :key="item" :label="item" :value="item" />
              </el-select>

              <el-select
                v-else-if="getFieldMeta(condition.field)?.field_type === 'boolean'"
                :model-value="String(Boolean(condition.value))"
                placeholder="选择布尔值"
                @update:model-value="handleConditionStaticValueChange(index, String($event) === 'true')"
              >
                <el-option label="是 / true" value="true" />
                <el-option label="否 / false" value="false" />
              </el-select>

              <el-input-number
                v-else-if="getFieldMeta(condition.field)?.field_type === 'number'"
                :model-value="typeof condition.value === 'number' ? condition.value : undefined"
                class="!w-full"
                :controls="false"
                placeholder="输入数值"
                @update:model-value="handleConditionStaticValueChange(index, typeof $event === 'number' ? $event : 0)"
              />

              <el-input
                v-else
                :model-value="normalizeValue(condition.value)"
                placeholder="输入固定值"
                @update:model-value="handleConditionStaticValueChange(index, String($event ?? ''))"
              />
            </template>

            <el-button plain type="danger" @click="removeCondition(index)">删除</el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-cyan-100/60">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">输出映射</div>
          <div class="mt-1 text-sm text-slate-500">控制感知结果如何进入 runtime state 与后续节点。</div>
        </div>
        <el-switch v-model="passRawPayload" inline-prompt active-text="保留原始" inactive-text="仅映射" />
      </div>

      <div class="space-y-3">
        <el-input v-model="outputEventName" placeholder="输出事件名，如 inventory.low_stock.detected" />
        <el-select v-model="selectedFields" class="w-full" multiple collapse-tags collapse-tags-tooltip placeholder="选择要透传的字段">
          <el-option v-for="field in availableFields" :key="field.value" :label="field.label" :value="field.value" />
        </el-select>
        <el-input
          v-model="outputMappingText"
          type="textarea"
          :rows="5"
          placeholder="item_id=payload.item_id&#10;stock_count=payload.stock_count&#10;event_type=event.event_type"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchSensorMetadata } from '@/api/workflows'
import type {
  SensorConditionConfig,
  SensorFieldOption,
  SensorMetadataResponse,
  SensorNodeConfig,
  SensorOperatorOption,
} from '@/types/workflow'

const props = defineProps<{
  modelValue: Record<string, unknown>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: SensorNodeConfig]
}>()

const logicOptions = [
  { label: '全部满足', value: 'and' },
  { label: '任一满足', value: 'or' },
]

const metadataLoading = ref(false)
const metadata = ref<SensorMetadataResponse>({
  source_types: [],
  operators: [],
  sources: [],
})

const currentConfig = computed<SensorNodeConfig>(() => {
  const config = props.modelValue as SensorNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    source_type: config.source_type ?? 'manual',
    source_system: config.source_system ?? '',
    source_table: config.source_table ?? '',
    source_event_key: config.source_event_key ?? '',
    selected_fields: config.selected_fields ?? [],
    condition_logic: config.condition_logic ?? 'and',
    conditions: config.conditions ?? [],
    output_event_name: config.output_event_name ?? '',
    output_mapping: config.output_mapping ?? {},
    pass_raw_payload: config.pass_raw_payload ?? true,
  }
})

const updateConfig = (patch: Partial<SensorNodeConfig>) => {
  emit('update:modelValue', {
    ...currentConfig.value,
    ...patch,
  })
}

const sourceType = computed({
  get: () => currentConfig.value.source_type ?? 'manual',
  set: (value: SensorNodeConfig['source_type']) => updateConfig({ source_type: value, source_system: '', source_table: '', source_event_key: '', selected_fields: [], conditions: [] }),
})

const sourceSystem = computed({
  get: () => currentConfig.value.source_system ?? '',
  set: (value: string) => updateConfig({ source_system: value, source_table: '', source_event_key: '', selected_fields: [], conditions: [] }),
})

const sourceTable = computed({
  get: () => currentConfig.value.source_table ?? '',
  set: (value: string) => updateConfig({ source_table: value, source_event_key: '', selected_fields: [], conditions: [] }),
})

const sourceEventKey = computed({
  get: () => currentConfig.value.source_event_key ?? '',
  set: (value: string) => updateConfig({ source_event_key: value }),
})

const conditionLogic = computed({
  get: () => currentConfig.value.condition_logic ?? 'and',
  set: (value: SensorNodeConfig['condition_logic']) => updateConfig({ condition_logic: value }),
})

const passRawPayload = computed({
  get: () => currentConfig.value.pass_raw_payload ?? true,
  set: (value: boolean) => updateConfig({ pass_raw_payload: value }),
})

const outputEventName = computed({
  get: () => currentConfig.value.output_event_name ?? '',
  set: (value: string) => updateConfig({ output_event_name: value }),
})

const selectedFields = computed({
  get: () => currentConfig.value.selected_fields ?? [],
  set: (value: string[]) => updateConfig({ selected_fields: value }),
})

const outputMappingText = computed({
  get: () =>
    Object.entries(currentConfig.value.output_mapping ?? {})
      .map(([key, path]) => `${key}=${path}`)
      .join('\n'),
  set: (value: string) => {
    const mapping = value
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
    updateConfig({ output_mapping: mapping })
  },
})

const sourceTypeOptions = computed(() => metadata.value.source_types)
const availableSources = computed(() => metadata.value.sources.filter((item) => item.source_type === sourceType.value))
const selectedSource = computed(() => availableSources.value.find((item) => item.value === sourceSystem.value) ?? null)
const availableTables = computed(() => selectedSource.value?.tables ?? [])
const selectedTable = computed(() => availableTables.value.find((item) => item.value === sourceTable.value) ?? null)
const availableEventKeys = computed(() => selectedTable.value?.event_keys ?? [])
const availableFields = computed(() => selectedTable.value?.fields ?? [])
const conditionRows = computed(() => currentConfig.value.conditions ?? [])

const getFieldMeta = (fieldName?: string) => availableFields.value.find((item) => item.value === fieldName)

const getOperatorOptions = (fieldName?: string): SensorOperatorOption[] => {
  const fieldType = getFieldMeta(fieldName)?.field_type
  if (!fieldType) {
    return metadata.value.operators
  }
  return metadata.value.operators.filter((item) => item.supported_field_types.includes(fieldType))
}

const normalizeValue = (value: unknown) => (value === undefined || value === null ? '' : String(value))
const getCompareMode = (condition: SensorConditionConfig) => (condition.value_from_field ? 'field' : 'value')

const updateCondition = (index: number, patch: Partial<SensorConditionConfig>) => {
  const nextConditions = [...conditionRows.value]
  const current = nextConditions[index] ?? { field: '', operator: 'eq' as const }
  nextConditions[index] = {
    ...current,
    ...patch,
  }
  updateConfig({ conditions: nextConditions })
}

const handleConditionFieldChange = (index: number, value: unknown) => {
  updateCondition(index, { field: String(value ?? ''), value: undefined, value_from_field: undefined })
}

const handleConditionOperatorChange = (index: number, value: unknown) => {
  updateCondition(index, { operator: value as SensorConditionConfig['operator'] })
}

const handleCompareModeChange = (index: number, value: unknown) => {
  setCompareMode(index, String(value ?? 'value'))
}

const handleConditionValueFieldChange = (index: number, value: unknown) => {
  updateCondition(index, { value_from_field: String(value ?? ''), value: undefined })
}

const handleConditionStaticValueChange = (index: number, value: string | number | boolean) => {
  updateCondition(index, { value, value_from_field: undefined })
}

const setCompareMode = (index: number, mode: string) => {
  if (mode === 'field') {
    updateCondition(index, { value: undefined, value_from_field: availableFields.value[0]?.value ?? '' })
    return
  }
  updateCondition(index, { value_from_field: undefined, value: undefined })
}

const addCondition = () => {
  const firstField = availableFields.value[0]
  const firstOperator = getOperatorOptions(firstField?.value)[0]?.value ?? 'eq'
  updateConfig({
    conditions: [
      ...conditionRows.value,
      {
        field: firstField?.value ?? '',
        operator: firstOperator,
      },
    ],
  })
}

const removeCondition = (index: number) => {
  updateConfig({ conditions: conditionRows.value.filter((_, itemIndex) => itemIndex !== index) })
}

const ensureSourceDefaults = () => {
  if (availableSources.value.length > 0 && !availableSources.value.some((item) => item.value === sourceSystem.value)) {
    sourceSystem.value = availableSources.value[0].value
    return
  }
  if (availableTables.value.length > 0 && !availableTables.value.some((item) => item.value === sourceTable.value)) {
    sourceTable.value = availableTables.value[0].value
    return
  }
  if (availableEventKeys.value.length > 0 && !availableEventKeys.value.some((item) => item.value === sourceEventKey.value)) {
    sourceEventKey.value = availableEventKeys.value[0].value
  }
}

watch([availableSources, availableTables, availableEventKeys], ensureSourceDefaults, { immediate: true })

watch(
  availableFields,
  (fields) => {
    if (fields.length === 0) {
      return
    }
    const validFieldSet = new Set(fields.map((item) => item.value))
    const nextSelectedFields = selectedFields.value.filter((item) => validFieldSet.has(item))
    const nextConditions = conditionRows.value
      .filter((item) => validFieldSet.has(item.field))
      .map((item) => ({
        ...item,
        ...(item.value_from_field && !validFieldSet.has(item.value_from_field) ? { value_from_field: fields[0].value } : {}),
      }))

    if (nextSelectedFields.length !== selectedFields.value.length || nextConditions.length !== conditionRows.value.length) {
      updateConfig({
        selected_fields: nextSelectedFields,
        conditions: nextConditions,
      })
    }
  },
  { immediate: true },
)

onMounted(async () => {
  metadataLoading.value = true
  try {
    const response = await fetchSensorMetadata()
    metadata.value = response.data
  } catch {
    ElMessage.error('加载感知源目录失败')
  } finally {
    metadataLoading.value = false
  }
})
</script>
