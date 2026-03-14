<template>
  <div class="rounded-2xl border border-cyan-500/20 bg-slate-950/80 p-4 shadow-[0_16px_40px_rgba(8,145,178,0.12)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">Parameter Completion</div>
        <div class="mt-1 text-sm font-semibold text-slate-100">{{ workflow.title }}</div>
        <div class="mt-1 text-xs leading-5 text-slate-400">
          补齐启动参数后，会沿用当前对话上下文继续启动该 workflow。
        </div>
      </div>
      <span class="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-2.5 py-1 text-[11px] text-cyan-100">
        {{ requiredFields.length }} 个必填
      </span>
    </div>

    <div class="mt-4 space-y-3">
      <div v-for="field in fields" :key="field.name" class="space-y-2">
        <div class="flex items-center justify-between gap-3">
          <label class="text-xs font-medium text-slate-200">{{ field.label }}</label>
          <span v-if="field.required" class="text-[11px] text-rose-300">必填</span>
        </div>

        <el-switch
          v-if="field.type === 'boolean'"
          v-model="booleanValues[field.name]"
          inline-prompt
          active-text="是"
          inactive-text="否"
        />

        <el-input-number
          v-else-if="field.type === 'number' || field.type === 'integer'"
          v-model="numberValues[field.name]"
          :min="0"
          controls-position="right"
          class="!w-full"
        />

        <el-input
          v-else
          v-model="textValues[field.name]"
          :type="field.multiline ? 'textarea' : 'text'"
          :rows="field.multiline ? 3 : undefined"
          :placeholder="field.placeholder"
        />

        <div v-if="field.description" class="text-[11px] leading-5 text-slate-500">{{ field.description }}</div>
      </div>
    </div>

    <div class="mt-4 flex items-center justify-between gap-3 border-t border-slate-800 pt-4">
      <div class="text-[11px] text-slate-500">参数仅用于本次启动；后端会继续做缺失字段校验。</div>
      <el-button type="primary" :loading="submitting" @click="submit">
        补齐参数并启动
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'

import { useChatSession } from '@/composables/useChatSession'
import type { WorkflowCatalogItem } from '@/types/chat'

type SchemaProperty = {
  title?: string
  description?: string
  type?: string
  format?: string
  placeholder?: string
}

type FieldConfig = {
  name: string
  label: string
  description: string
  type: string
  placeholder: string
  multiline: boolean
  required: boolean
}

const props = defineProps<{
  workflow: WorkflowCatalogItem
  source: string
  sourceMessageId?: string
  missingInputs?: string[]
}>()

const { startSelectedWorkflow } = useChatSession()
const textValues = reactive<Record<string, string>>({})
const numberValues = reactive<Record<string, number | undefined>>({})
const booleanValues = reactive<Record<string, boolean>>({})

const requiredFields = computed(() => props.missingInputs?.length ? props.missingInputs : props.workflow.required_inputs ?? [])

const fields = computed<FieldConfig[]>(() => {
  const schema = (props.workflow.input_schema ?? {}) as Record<string, unknown>
  const properties = ((schema.properties ?? {}) as Record<string, SchemaProperty>)
  const requiredSet = new Set(requiredFields.value)
  const names = requiredFields.value.length > 0 ? requiredFields.value : Object.keys(properties)

  return names.map((name) => {
    const property = properties[name] ?? {}
    const label = property.title || name
    const description = property.description || ''
    const type = property.type || 'string'
    const placeholder = property.placeholder || `请输入${label}`
    const multiline = property.format === 'textarea' || /remark|note|reason|description/i.test(name)
    return {
      name,
      label,
      description,
      type,
      placeholder,
      multiline,
      required: requiredSet.has(name),
    }
  })
})

const submitting = computed(() => false)

const submit = async () => {
  const inputValues: Record<string, string | number | boolean> = {}

  for (const field of fields.value) {
    if (field.type === 'boolean') {
      inputValues[field.name] = booleanValues[field.name] ?? false
      continue
    }

    if (field.type === 'number' || field.type === 'integer') {
      const value = numberValues[field.name]
      if (value === undefined && field.required) {
        ElMessage.warning(`请先填写 ${field.label}`)
        return
      }
      if (value !== undefined) {
        inputValues[field.name] = value
      }
      continue
    }

    const value = (textValues[field.name] ?? '').trim()
    if (!value && field.required) {
      ElMessage.warning(`请先填写 ${field.label}`)
      return
    }
    if (value) {
      inputValues[field.name] = value
    }
  }

  await startSelectedWorkflow(
    props.workflow.workflow_id,
    props.source,
    props.sourceMessageId,
    inputValues,
    `补齐参数后启动工作流：${props.workflow.title}`,
  )
}
</script>
