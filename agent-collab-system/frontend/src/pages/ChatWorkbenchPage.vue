<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 p-6">
    <h1 class="mb-6 text-2xl font-semibold">智能体协同对话工作台</h1>
    <div class="grid grid-cols-[280px_1fr] gap-4">
      <ChatSidebar />
      <div class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <ChatWindow />
        <div class="my-4">
          <ApprovalCard />
        </div>
        <MessageComposer />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ApprovalCard from '@/components/chat/ApprovalCard.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import MessageComposer from '@/components/chat/MessageComposer.vue'
</script>
