<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#edf3fb_0%,#f8fbff_44%,#eef2f7_100%)] p-6 text-slate-900">
    <WorkspaceTopNav
      title="对话区"
      description="中间主区域就是 AI 对话框；审批、流程目录、执行结果作为侧边辅助区存在。"
    />
    <div class="overflow-hidden rounded-[30px] border border-slate-200/80 bg-white/95 shadow-[0_28px_80px_rgba(15,23,42,0.10)]">
      <div class="border-b border-slate-200/80 px-6 py-5">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div class="text-[11px] uppercase tracking-[0.32em] text-sky-700/70">部门 AI 对话工作台</div>
            <div class="mt-2 text-[28px] font-semibold tracking-tight text-slate-950">AI 对话主窗口</div>
            <div class="mt-1 text-sm text-slate-500">用户在中间主对话区直接提问，AI 负责回答问题；部门流程、审批和执行结果只作为辅助能力围绕主对话展开。</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <div class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-500">主区域优先展示 AI 问答</div>
            <div class="rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700">默认模型：Gemini 中转站</div>
          </div>
        </div>
      </div>
      <div class="grid items-start gap-4 px-6 py-5 xl:grid-cols-[320px_minmax(0,1.45fr)_300px]">
        <div class="space-y-4">
          <ChatIdentityPanel />
          <ChatSidebar />
        </div>
        <div class="min-w-0 rounded-[28px] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff_0%,#f8fbff_100%)] p-4 shadow-[0_24px_60px_rgba(148,163,184,0.12)] xl:h-[930px] xl:min-h-[930px] xl:max-h-[930px] xl:flex xl:flex-col">
          <ChatWindow class="xl:flex-1" />
          <div class="mt-4 rounded-[22px] border border-slate-200 bg-white px-4 py-4 shadow-sm shadow-slate-200/60">
            <div class="mb-3 text-[11px] uppercase tracking-[0.22em] text-slate-500">发送消息给 AI</div>
            <MessageComposer />
          </div>
        </div>
        <div class="space-y-4">
          <DepartmentWorkflowCatalog />
          <OperationsCenter />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import ChatIdentityPanel from '@/components/chat/ChatIdentityPanel.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import DepartmentWorkflowCatalog from '@/components/chat/DepartmentWorkflowCatalog.vue'
import OperationsCenter from '@/components/chat/OperationsCenter.vue'
import WorkspaceTopNav from '@/components/layout/WorkspaceTopNav.vue'
import MessageComposer from '@/components/chat/MessageComposer.vue'
import { useChatSession } from '@/composables/useChatSession'

const { initialize } = useChatSession()

onMounted(async () => {
  await initialize()
})
</script>
