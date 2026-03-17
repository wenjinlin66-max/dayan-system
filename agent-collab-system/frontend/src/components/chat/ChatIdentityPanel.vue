<template>
  <div class="rounded-[24px] border border-slate-200/80 bg-white/95 p-4 shadow-[0_18px_40px_rgba(148,163,184,0.10)]">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">对话身份</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">账号与可见范围</div>
      </div>
      <span class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] text-slate-500">
        {{ chatStore.canViewAllDepartments() ? 'CEO / 全局查看' : '部门账号' }}
      </span>
    </div>

    <div class="space-y-3">
      <div class="rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-3 text-sm text-slate-700">
        <div class="font-medium text-slate-900">{{ authStore.identity?.display_name || chatStore.activeProfile.label }}</div>
        <div class="mt-1 text-xs text-slate-500">user_id: {{ authStore.identity?.user_id || chatStore.activeProfile.userId }} · dept: {{ getDepartmentLabel(authStore.identity?.dept_id || chatStore.getEffectiveDeptId()) }}</div>
      </div>

      <div v-if="chatStore.canViewAllDepartments()" class="grid gap-3 md:grid-cols-2">
        <div>
          <div class="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">查看范围</div>
          <el-segmented v-model="scopeMode" :options="scopeOptions" block />
        </div>
        <div>
          <div class="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">聚焦部门</div>
          <el-select v-model="scopeDeptId" class="w-full" placeholder="全部部门">
            <el-option label="全部部门" value="" />
            <el-option v-for="item in deptOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
      </div>

      <div class="rounded-2xl border border-sky-100 bg-sky-50/70 px-4 py-3 text-xs leading-6 text-slate-600">
        <div>当前账号：<span class="font-medium text-slate-900">{{ chatStore.activeProfile.label }}</span></div>
        <div>当前部门：<span class="font-medium text-slate-900">{{ getDepartmentLabel(chatStore.getEffectiveDeptId()) }}</span></div>
        <div>{{ helperText }}</div>
      </div>

      <el-button plain class="w-full" @click="logout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useChatSession } from '@/composables/useChatSession'
import { useAuthStore } from '@/store/auth'
import { useChatStore } from '@/store/chat'
import type { ChatScopeMode } from '@/utils/chatIdentity'
import { ERP_DEPARTMENT_OPTIONS, getDepartmentLabel } from '@/utils/erpDepartments'

const chatStore = useChatStore()
const authStore = useAuthStore()
const router = useRouter()
const { reloadForContextChange } = useChatSession()

const deptOptions = ERP_DEPARTMENT_OPTIONS.filter((item) => item.value !== 'ceo')
const scopeOptions = [
  { label: '单部门', value: 'department' },
  { label: '全部部门', value: 'all_departments' },
]

const scopeMode = computed({
  get: () => chatStore.scopeMode,
  set: async (value: ChatScopeMode) => {
    chatStore.applyScopeMode(value)
    await reloadForContextChange()
  },
})

const scopeDeptId = computed({
  get: () => chatStore.scopeDeptId,
  set: async (value: string) => {
    chatStore.applyScopeDeptId(value)
    await reloadForContextChange()
  },
})

const helperText = computed(() => {
  if (!chatStore.canViewAllDepartments()) {
    return '部门账号只能查看并使用自己部门下的对话会话。'
  }
  return chatStore.scopeMode === 'all_departments'
    ? 'CEO 可总览全部部门会话；如果再选具体部门，可进一步聚焦该部门的会话、流程与审批。'
    : 'CEO 当前按单部门视角工作，可直接切到指定部门的对话区。'
})

const logout = async () => {
  authStore.clearSession()
  await router.replace('/login')
}
</script>
