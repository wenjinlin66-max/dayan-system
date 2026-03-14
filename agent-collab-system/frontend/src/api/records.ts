import { http } from './client'

import type {
  RecordMutationResponse,
  RecentRecordEventsResponse,
  RecordsRowListResponse,
  RecordsSourcesResponse,
  RecordsTableSchemaResponse,
  RecordsTablesResponse,
} from '@/types/records'

export const fetchRecordSources = async () => http.get<RecordsSourcesResponse>('/v1/records/sources')
export const fetchRecordTables = async () => http.get<RecordsTablesResponse>('/v1/records/tables')
export const fetchRecordTableSchema = async (tableName: string) => http.get<RecordsTableSchemaResponse>(`/v1/records/tables/${tableName}/schema`)
export const fetchRecordRows = async (tableName: string) => http.get<RecordsRowListResponse>(`/v1/records/tables/${tableName}/rows`)
export const createRecordRow = async (tableName: string, values: Record<string, unknown>) =>
  http.post<RecordMutationResponse>(`/v1/records/tables/${tableName}/rows`, { values })
export const updateRecordRow = async (tableName: string, recordId: string, values: Record<string, unknown>) =>
  http.put<RecordMutationResponse>(`/v1/records/tables/${tableName}/rows/${recordId}`, { values })
export const deleteRecordRow = async (tableName: string, recordId: string) =>
  http.delete<RecordMutationResponse>(`/v1/records/tables/${tableName}/rows/${recordId}`)
export const fetchRecentRecordEvents = async () => http.get<RecentRecordEventsResponse>('/v1/records/events/recent')
