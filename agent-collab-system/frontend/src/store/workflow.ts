import { defineStore } from 'pinia'

export const useWorkflowStore = defineStore('workflow', {
  state: () => ({
    currentWorkflowId: '' as string,
  }),
})
