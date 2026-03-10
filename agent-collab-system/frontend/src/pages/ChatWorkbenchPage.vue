<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 p-6">
    <h1 class="mb-6 text-2xl font-semibold">智能体协同对话工作台</h1>
    <div class="grid grid-cols-[280px_1fr_320px] gap-4">
      <ChatSidebar />
      <div class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <ChatWindow />
        <div class="my-4">
          <ExecutionResultCard />
        </div>
        <AttachmentPanel class="mb-4" />
        <MessageComposer />
      </div>
      <div class="space-y-4">
        <DepartmentWorkflowCatalog />
        <ApprovalWorkbench />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ApprovalWorkbench from '@/components/chat/ApprovalWorkbench.vue'
import AttachmentPanel from '@/components/chat/AttachmentPanel.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import DepartmentWorkflowCatalog from '@/components/chat/DepartmentWorkflowCatalog.vue'
import ExecutionResultCard from '@/components/chat/ExecutionResultCard.vue'
import MessageComposer from '@/components/chat/MessageComposer.vue'
</script>
