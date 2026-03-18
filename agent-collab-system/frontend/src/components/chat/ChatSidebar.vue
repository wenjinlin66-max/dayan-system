<template>
  <div class="rounded-[28px] border border-slate-200/80 bg-white/95 p-4 shadow-[0_20px_50px_rgba(148,163,184,0.12)]">
    <div class="mb-4 rounded-[22px] border border-sky-200 bg-[linear-gradient(135deg,#f0f7ff,#edf8ff)] px-4 py-4">
        <div class="text-[11px] uppercase tracking-[0.22em] text-sky-700/70">{{ chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments' ? 'CEO 对话总览' : '当前部门对话框' }}</div>
        <div class="mt-2 text-lg font-semibold text-slate-950">{{ currentDeptLabel }}</div>
        <div class="mt-1 text-xs leading-6 text-slate-600">{{ panelDescription }}</div>
      </div>

    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">部门会话列表</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">{{ chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments' ? '跨部门历史会话' : '当前部门的历史对话框' }}</div>
      </div>
      <el-button size="small" type="primary" @click="createNewSession">新建会话</el-button>
    </div>

    <div class="space-y-2">
      <div
        v-for="session in visibleSessions"
        :key="session.session_id"
        class="group rounded-2xl border px-3 py-3 text-sm transition"
        :class="session.session_id === currentSessionId ? 'border-sky-300 bg-sky-50 text-sky-900 shadow-sm shadow-sky-100/80' : 'border-slate-200 bg-slate-50/70 text-slate-700 hover:bg-white'"
      >
        <div class="flex items-start justify-between gap-3">
          <button class="min-w-0 flex-1 text-left" @click="handleSelectSession(session.session_id)">
            <div class="truncate font-medium">{{ session.title }}</div>
            <div class="mt-1 text-xs text-slate-500">{{ getDepartmentLabel(session.dept_id) }} · {{ session.last_message_at ? formatTime(session.last_message_at) : '刚创建' }}</div>
          </button>
          <el-button
            text
            type="danger"
            size="small"
            class="opacity-100 md:opacity-0 md:group-hover:opacity-100"
            @click.stop="handleDeleteSession(session.session_id)"
          >
            删除
          </el-button>
        </div>
      </div>

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
        <div
          v-for="session in sessions"
          :key="`dialog-${session.session_id}`"
          class="group rounded-2xl border px-4 py-3 transition"
          :class="session.session_id === currentSessionId ? 'border-sky-300 bg-sky-50 text-sky-900 shadow-sm shadow-sky-100/80' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'"
        >
          <div class="flex items-start justify-between gap-3">
            <button class="min-w-0 flex-1 text-left" @click="handleSelectFromHistory(session.session_id)">
              <div class="truncate font-medium">{{ session.title }}</div>
              <div class="mt-1 text-xs text-slate-500">{{ session.last_message_at ? formatTime(session.last_message_at) : '刚创建' }}</div>
            </button>
            <el-button text type="danger" size="small" @click.stop="handleDeleteSession(session.session_id)">删除</el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { useChatSession } from '@/composables/useChatSession'
import { useChatStore } from '@/store/chat'
import { formatDateTime } from '@/utils/dateTime'
import { getDepartmentLabel } from '@/utils/erpDepartments'

const chatStore = useChatStore()
const sessions = computed(() => chatStore.sessions)
const currentSessionId = computed(() => chatStore.currentSessionId)
const currentDeptLabel = computed(() => chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments'
  ? (chatStore.scopeDeptId ? `${getDepartmentLabel(chatStore.scopeDeptId)} · CEO 视角` : '全部部门 · CEO 视角')
  : `${getDepartmentLabel(chatStore.currentDeptId || chatStore.getEffectiveDeptId())}`)
const panelDescription = computed(() => chatStore.canViewAllDepartments() && chatStore.scopeMode === 'all_departments'
  ? 'CEO 可跨部门查看会话与执行结果；点击具体会话后会自动切入对应部门消息流。'
  : '该部门会话统一承接审批提醒、执行结果回传和本部门流程调用。')
const { selectSession, createSession, deleteSession } = useChatSession()
const historyDialogVisible = ref(false)
const historyPreviewLimit = 4
const visibleSessions = computed(() => sessions.value.slice(0, historyPreviewLimit))

const formatTime = (value: string) => formatDateTime(value)

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

const handleDeleteSession = async (sessionId: string) => {
  try {
    await ElMessageBox.confirm('删除后该历史会话及消息记录将不可恢复，确认继续？', '删除历史会话', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await deleteSession(sessionId)
    ElMessage.success('历史会话已删除')
    if (historyDialogVisible.value && sessions.value.length <= historyPreviewLimit) {
      historyDialogVisible.value = false
    }
  } catch (error) {
    ElMessage.error(`删除历史会话失败：${String(error)}`)
  }
}
</script>

<style scoped>
:deep(.chat-history-dialog .el-dialog) {
  border-radius: 24px;
}
</style>
