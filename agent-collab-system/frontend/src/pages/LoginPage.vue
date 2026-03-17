<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#eef4fb_0%,#f8fbff_48%,#edf1f7_100%)] px-6 py-10 text-slate-900">
    <div class="mx-auto max-w-5xl grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div class="rounded-[32px] border border-slate-200/80 bg-white/90 p-8 shadow-[0_24px_80px_rgba(15,23,42,0.10)]">
        <div class="text-[11px] uppercase tracking-[0.32em] text-sky-700/70">Dayan Login</div>
        <h1 class="mt-3 text-4xl font-semibold tracking-tight text-slate-950">大衍部门对话区登录</h1>
        <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-600">这一步开始用真实账号会话进入系统，不再依赖前端手动伪造 header。部门账号只能看自己的对话区，CEO 账号可以总览全部门。</p>

        <div class="mt-8 grid gap-3 md:grid-cols-2">
          <div v-for="account in sampleAccounts" :key="account.username" class="rounded-[24px] border border-slate-200 bg-slate-50/70 p-4">
            <div class="text-sm font-semibold text-slate-900">{{ account.label }}</div>
            <div class="mt-2 text-xs leading-6 text-slate-500">账号：{{ account.username }}<br />密码：{{ account.password }}</div>
            <el-button class="mt-3" size="small" plain @click="applyAccount(account.username, account.password)">填入该账号</el-button>
          </div>
        </div>
      </div>

      <div class="rounded-[32px] border border-slate-200/80 bg-white/95 p-8 shadow-[0_24px_80px_rgba(15,23,42,0.10)]">
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">登录表单</div>
        <div class="mt-2 text-2xl font-semibold text-slate-950">选择账号进入</div>
        <div class="mt-6 space-y-4">
          <el-input v-model="username" placeholder="输入账号，例如 production.li" />
          <el-input v-model="password" type="password" show-password placeholder="输入密码" @keydown.enter="handleLogin" />
          <el-alert v-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
          <el-button type="primary" class="w-full" :loading="loginSubmitting" @click="handleLogin">登录进入工作台</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

import { login } from '@/api/auth'
import { useAuthStore } from '@/store/auth'
import { useChatStore } from '@/store/chat'
import { resolveProfileIdFromIdentity } from '@/utils/chatIdentity'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const username = ref('production.li')
const password = ref('dayan-prod-123')
const errorMessage = ref('')
const loginSubmitting = computed(() => authStore.loginSubmitting)

const sampleAccounts = [
  { label: '生产部 / 李工', username: 'production.li', password: 'dayan-prod-123' },
  { label: '仓储部 / 王仓', username: 'warehouse.wang', password: 'dayan-warehouse-123' },
  { label: '供应链部 / 周链', username: 'supply.zhou', password: 'dayan-supply-123' },
  { label: 'CEO / 全局查看', username: 'ceo.demo', password: 'dayan-ceo-123' },
]

const applyAccount = (nextUsername: string, nextPassword: string) => {
  username.value = nextUsername
  password.value = nextPassword
  errorMessage.value = ''
}

const handleLogin = async () => {
  errorMessage.value = ''
  authStore.setLoginSubmitting(true)
  try {
    const response = await login({ username: username.value, password: password.value })
    authStore.setSession(response.data)
    chatStore.syncIdentityFromAuth({
      userId: response.data.identity.user_id,
      deptId: response.data.identity.dept_id,
      roles: response.data.identity.roles,
      profileId: resolveProfileIdFromIdentity(response.data.identity),
    })
    await router.replace('/chat-workbench')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : `登录失败：${String(error)}`
  } finally {
    authStore.setLoginSubmitting(false)
  }
}
</script>
