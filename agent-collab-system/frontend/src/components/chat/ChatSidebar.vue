<template>
  <div class="rounded-[28px] border border-slate-200/80 bg-white/95 p-4 shadow-[0_20px_50px_rgba(148,163,184,0.12)]">
    <div class="mb-4 rounded-[22px] border border-sky-200 bg-[linear-gradient(135deg,#f0f7ff,#edf8ff)] px-4 py-4">
      <div class="text-[11px] uppercase tracking-[0.22em] text-sky-700/70">当前部门对话框</div>
      <div class="mt-2 text-lg font-semibold text-slate-950">{{ currentDeptLabel }}</div>
      <div class="mt-1 text-xs leading-6 text-slate-600">该部门会话统一承接审批提醒、执行结果回传和本部门流程调用。</div>
    </div>

    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">部门会话列表</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">当前部门的历史对话框</div>
      </div>
      <el-button size="small" type="primary" @click="createNewSession">新建会话</el-button>
    </div>

    <div class="space-y-2">
      <button
        v-for="session in visibleSessions"
        :key="session.session_id"
        class="w-full rounded-2xl border px-3 py-3 text-left text-sm transition"
        :class="session.session_id === currentSessionId ? 'border-sky-300 bg-sky-50 text-sky-900 shadow-sm shadow-sky-100/80' : 'border-slate-200 bg-slate-50/70 text-slate-700 hover:bg-white'"
        @click="handleSelectSession(session.session_id)"
      >
        <div class="font-medium">{{ session.title }}</div>
        <div class="mt-1 text-xs text-slate-500">{{ session.dept_id }} · {{ session.last_message_at ? formatTime(session.last_message_at) : '刚创建' }}</div>
      </button>

      <button
        v-if="sessions.length > historyPreviewLimit"
        class="w-full rounded-2xl border border-slate-200 bg-white px-3 py-3 text-left text-sm text-slate-700 transition hover:bg-slate-50"
        @click="historyDialogVisible = true"
      >
        <div class="font-medium">查看全部历史</div>
        <div class="mt-1 text-xs text-slate-500">打开中间弹窗选择历史记录</div>
      </button>
    </div>

    <el-dialog v-model="historyDialogVisible" width="560px" align-center class="chat-history-dialog">
      <template #header>
        <div>
          <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">历史会话</div>
          <div class="mt-1 text-lg font-semibold text-slate-950">选择要恢复的对话记录</div>
        </div>
      </template>

      <div class="space-y-2">
        <button
          v-for="session in sessions"
          :key="`dialog-${session.session_id}`"
          class="w-full rounded-2xl border px-4 py-3 text-left transition"
          :class="session.session_id === currentSessionId ? 'border-sky-300 bg-sky-50 text-sky-900 shadow-sm shadow-sky-100/80' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'"
          @click="handleSelectFromHistory(session.session_id)"
        >
          <div class="font-medium">{{ session.title }}</div>
          <div class="mt-1 text-xs text-slate-500">{{ session.last_message_at ? formatTime(session.last_message_at) : '刚创建' }}</div>
        </button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { useChatSession } from '@/composables/useChatSession'
import { useChatStore } from '@/store/chat'

const chatStore = useChatStore()
const sessions = computed(() => chatStore.sessions)
const currentSessionId = computed(() => chatStore.currentSessionId)
const currentDeptLabel = computed(() => `${chatStore.currentDeptId || 'default'} 部门`)
const { selectSession, createSession } = useChatSession()
const historyDialogVisible = ref(false)
const historyPreviewLimit = 4
const visibleSessions = computed(() => sessions.value.slice(0, historyPreviewLimit))

const formatTime = (value: string) => new Date(value).toLocaleString('zh-CN', { hour12: false })

const handleSelectSession = async (sessionId: string) => {
  await selectSession(sessionId)
}

const handleSelectFromHistory = async (sessionId: string) => {
  await selectSession(sessionId)
  historyDialogVisible.value = false
}

const createNewSession = async () => {
  await createSession()
}
</script>

<style scoped>
:deep(.chat-history-dialog .el-dialog) {
  border-radius: 24px;
}
</style>
