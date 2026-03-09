import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    currentSessionId: '' as string,
  }),
})
