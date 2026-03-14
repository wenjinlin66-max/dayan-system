<template>
  <div class="space-y-3">
    <el-input v-model="content" type="textarea" :rows="4" resize="none" placeholder="直接向 AI 提问，或描述你想让当前部门执行的任务。Shift+Enter 可继续换行，Enter 发送。" @keydown.enter="handleKeydown" />
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="text-xs text-slate-500">主对话区优先处理问答；如命中部门 workflow，会继续给出流程候选与执行结果。</div>
      <el-button type="primary" :loading="sending" @click="handleSend">发送给 AI</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { useChatSession } from '@/composables/useChatSession'
import { useChatStore } from '@/store/chat'

const content = ref('')
const chatStore = useChatStore()
const sending = computed(() => chatStore.sending)
const { sendMessage } = useChatSession()

const handleSend = async () => {
  if (!content.value.trim()) {
    return
  }
  const message = content.value
  content.value = ''
  await sendMessage(message)
}

const handleKeydown = async (event: KeyboardEvent) => {
  if (event.shiftKey) {
    return
  }
  event.preventDefault()
  await handleSend()
}
</script>
