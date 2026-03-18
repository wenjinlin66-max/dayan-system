<template>
  <div class="rounded-[26px] border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f7fbff_100%)] p-4 min-h-[620px] text-sm text-slate-700 shadow-[0_16px_36px_rgba(148,163,184,0.10)] xl:flex xl:min-h-0 xl:h-full xl:flex-col">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-[22px] border border-slate-200 bg-slate-50/80 px-4 py-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">AI 对话消息流</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">这里优先承接用户提问与 AI 回答</div>
      </div>
      <div class="flex items-center gap-2">
        <div class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">共 {{ messages.length }} 条消息</div>
        <div class="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs text-violet-700">Gemini Proxy</div>
      </div>
    </div>

    <div v-if="messages.length === 0" class="flex min-h-[500px] items-center justify-center rounded-[22px] border border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-slate-500 xl:flex-1 xl:min-h-0">发送一条消息，开始当前部门的问答、审批或流程启动。</div>
    <div v-else class="max-h-[500px] space-y-3 overflow-y-auto pr-1 xl:flex-1 xl:max-h-none xl:min-h-0">
      <div
        v-for="message in messages"
        :key="message.message_id"
        class="rounded-[22px] border px-4 py-4"
        :class="message.role === 'user' ? 'ml-16 border-slate-200 bg-slate-50' : 'mr-16 border-sky-200 bg-sky-50/70 shadow-sm shadow-sky-100/70'"
      >
        <div class="mb-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span>{{ message.role === 'user' ? '你' : '部门助手' }}</span>
          <span v-if="showDeptBadge(message)" class="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[11px] text-slate-500">{{ message.dept_id }}</span>
          <span v-if="message.payload?.message_kind" class="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[11px] text-slate-500">{{ String(message.payload?.message_kind) }}</span>
          <span v-if="formatMessageTime(message)" class="text-[11px] text-slate-400">{{ formatMessageTime(message) }}</span>
        </div>
        <div class="whitespace-pre-wrap leading-8 text-slate-800">{{ message.content }}</div>

        <WorkflowParameterCard
          v-if="parameterWorkflow(message)"
          class="mt-3"
          :workflow="parameterWorkflow(message)!"
          source="parameter_completion"
          :source-message-id="message.message_id"
          :missing-inputs="missingInputs(message)"
        />

        <div v-if="candidateWorkflows(message).length > 0" class="mt-3 flex flex-wrap gap-2">
          <el-button
            v-for="candidate in candidateWorkflows(message)"
            :key="candidate.workflow_id"
            size="small"
            plain
            :loading="startingWorkflowId === candidate.workflow_id"
            :disabled="shouldShowInlineParameterCard(message, candidate.workflow_id)"
            @click="startWorkflow(candidate.workflow_id, message.message_id)"
          >
            {{ candidate.required_inputs?.length ? `填写参数后启动 ${candidate.title}` : `启动 ${candidate.title}` }}
          </el-button>
        </div>

        <div v-if="message.related_execution_id" class="mt-2 text-xs text-emerald-600">
          execution_id: {{ message.related_execution_id }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useChatSession } from '@/composables/useChatSession'
import { useChatStore } from '@/store/chat'
import type { ChatMessage, WorkflowCatalogItem } from '@/types/chat'
import { formatDateTime } from '@/utils/dateTime'
import WorkflowParameterCard from './WorkflowParameterCard.vue'

const chatStore = useChatStore()
const messages = computed(() => chatStore.messages)
const startingWorkflowId = computed(() => chatStore.startingWorkflowId)
const { startSelectedWorkflow } = useChatSession()
const showDeptBadge = (message: ChatMessage) => chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments' && Boolean(message.dept_id)

const candidateWorkflows = (message: ChatMessage): WorkflowCatalogItem[] => {
  const raw = message.payload?.candidate_workflows
  if (!Array.isArray(raw)) {
    return []
  }
  const deduped = new Map<string, WorkflowCatalogItem>()
  for (const item of raw as WorkflowCatalogItem[]) {
    if (!item?.workflow_id) {
      continue
    }
    if (!deduped.has(item.workflow_id)) {
      deduped.set(item.workflow_id, item)
    }
  }
  return Array.from(deduped.values())
}

const missingInputs = (message: ChatMessage): string[] => {
  const raw = message.payload?.missing_inputs
  return Array.isArray(raw) ? raw.filter((item): item is string => typeof item === 'string') : []
}

const parameterWorkflow = (message: ChatMessage): WorkflowCatalogItem | null => {
  const candidates = candidateWorkflows(message)
  return missingInputs(message).length > 0 && candidates.length === 1 ? candidates[0] : null
}

const shouldShowInlineParameterCard = (message: ChatMessage, workflowId: string) => {
  return parameterWorkflow(message)?.workflow_id === workflowId
}

const startWorkflow = async (workflowId: string, sourceMessageId: string) => {
  await startSelectedWorkflow(workflowId, 'candidate_confirmation', sourceMessageId)
}

const formatMessageTime = (message: ChatMessage) => {
  if (!message.created_at) {
    return ''
  }
  return formatDateTime(message.created_at, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>
