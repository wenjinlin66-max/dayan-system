export interface RecordsSourceItem {
  source_system: string
  label: string
}

export interface RecordsSourcesResponse {
  sources: RecordsSourceItem[]
}

export interface RecordsTableItem {
  table_name: string
  label: string
  source_system: string
  description: string
}

export interface RecordsTablesResponse {
  tables: RecordsTableItem[]
}

export interface RecordsTableSchemaField {
  name: string
  label: string
  field_type: string
  editable: boolean
}

export interface RecordsTableSchemaResponse {
  table_name: string
  label: string
  source_system: string
  fields: RecordsTableSchemaField[]
}

export interface RecordsRowListResponse {
  table_name: string
  rows: Record<string, unknown>[]
}

export interface RecordMutationResponse {
  table_name: string
  record_id: string
  row: Record<string, unknown>
  change_event_id: string
  triggered_execution_ids: string[]
}

export interface RecentRecordEvent {
  change_event_id: string
  table_name: string
  record_id: string
  operation: string
  event_type: string
  changed_fields: string[]
  triggered_execution_ids: string[]
  created_at?: string | null
}

export interface RecentRecordEventsResponse {
  events: RecentRecordEvent[]
}
