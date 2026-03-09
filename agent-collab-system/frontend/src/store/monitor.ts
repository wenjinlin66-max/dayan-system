import { defineStore } from 'pinia'

export const useMonitorStore = defineStore('monitor', {
  state: () => ({
    lastRefreshAt: '' as string,
  }),
})
