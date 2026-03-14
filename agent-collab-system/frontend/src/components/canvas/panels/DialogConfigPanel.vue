<template>
  <div class="space-y-4 rounded-[26px] border border-violet-200/80 bg-[linear-gradient(180deg,#faf8ff_0%,#f4f0ff_100%)] p-5 shadow-[0_18px_45px_rgba(139,92,246,0.10)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-violet-600/80">对话智能体</div>
        <div class="mt-1 text-base font-semibold text-slate-900">意图识别与响应风格</div>
        <div class="mt-1 text-sm leading-6 text-slate-500">配置用户对话入口的提示语、意图标签、响应方式与记忆强度。</div>
      </div>
      <span class="rounded-full border border-violet-300 bg-white px-3 py-1 text-[11px] font-medium text-violet-700">dialog_agent</span>
    </div>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-violet-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">入口提示</div>
      <div class="space-y-3">
        <el-input v-model="promptHint" placeholder="提示语 / 命令说明，如 帮我发起补货申请" />
        <el-input v-model="intentTag" placeholder="意图标签，如 command.start.replenishment" />
      </div>
    </section>

    <section class="rounded-2xl border border-white/80 bg-white/92 p-4 shadow-sm shadow-violet-100/60">
      <div class="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">响应与记忆</div>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">响应风格</div>
          <el-segmented v-model="responseStyle" :options="responseStyleOptions" block />
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">记忆强度</div>
          <el-segmented v-model="memoryProfile" :options="memoryOptions" block />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { DialogNodeConfig } from '@/types/workflow'

const props = defineProps<{ modelValue: Record<string, unknown> }>()
const emit = defineEmits<{ 'update:modelValue': [value: DialogNodeConfig] }>()

const responseStyleOptions = [
  { label: '引导式', value: 'guide' },
  { label: '确认式', value: 'confirm' },
  { label: '解释式', value: 'explain' },
]

const memoryOptions = [
  { label: '轻量', value: 'light' },
  { label: '标准', value: 'standard' },
  { label: '深度', value: 'deep' },
]

const currentConfig = computed<DialogNodeConfig>(() => {
  const config = props.modelValue as DialogNodeConfig
  return {
    description: typeof config.description === 'string' ? config.description : '',
    promptHint: config.promptHint ?? '',
    intentTag: config.intentTag ?? '',
    responseStyle: config.responseStyle ?? 'guide',
    memoryProfile: config.memoryProfile ?? 'standard',
  }
})

const updateConfig = (patch: Partial<DialogNodeConfig>) => {
  emit('update:modelValue', {
    ...currentConfig.value,
    ...patch,
  })
}

const promptHint = computed({
  get: () => currentConfig.value.promptHint ?? '',
  set: (value: string) => updateConfig({ promptHint: value }),
})

const intentTag = computed({
  get: () => currentConfig.value.intentTag ?? '',
  set: (value: string) => updateConfig({ intentTag: value }),
})

const responseStyle = computed({
  get: () => currentConfig.value.responseStyle ?? 'guide',
  set: (value: DialogNodeConfig['responseStyle']) => updateConfig({ responseStyle: value }),
})

const memoryProfile = computed({
  get: () => currentConfig.value.memoryProfile ?? 'standard',
  set: (value: DialogNodeConfig['memoryProfile']) => updateConfig({ memoryProfile: value }),
})
</script>
