import { defineStore } from 'pinia'

import type { RecentRecordEvent, RecordsRowListResponse, RecordsSourceItem, RecordsTableItem, RecordsTableSchemaResponse } from '@/types/records'

export const useRecordsStore = defineStore('records', {
  state: () => ({
    sources: [] as RecordsSourceItem[],
    tables: [] as RecordsTableItem[],
    currentTable: '' as string,
    currentSchema: null as RecordsTableSchemaResponse | null,
    currentRows: [] as RecordsRowListResponse['rows'],
    recentEvents: [] as RecentRecordEvent[],
    lastMutationSummary: '' as string,
  }),
})
