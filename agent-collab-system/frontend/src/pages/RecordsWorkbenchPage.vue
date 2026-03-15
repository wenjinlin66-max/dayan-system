<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#ecf6ff_0%,#f8fbff_42%,#eef2f7_100%)] p-6 text-slate-900">
    <WorkspaceTopNav title="业务表格区" description="临时测试工作区：查看 dayan_mock_records 中的真实业务表，改表后直接触发感知型工作流并观察写回结果。" />

    <div class="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_360px]">
      <aside class="rounded-[28px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_22px_60px_rgba(15,23,42,0.08)]">
        <div class="text-[11px] uppercase tracking-[0.24em] text-cyan-700/75">Source & Tables</div>
        <div class="mt-3 rounded-2xl border border-cyan-100 bg-cyan-50/70 px-3 py-2 text-sm text-cyan-900">
          <div class="font-medium">{{ currentSourceLabel }}</div>
          <div class="mt-1 text-xs text-cyan-700/80">当前是临时测试底座，后续 Go 正式接管后将整体删除。</div>
        </div>

        <div class="mt-4 space-y-2">
          <button
            v-for="table in tables"
            :key="table.table_name"
            class="w-full rounded-[22px] border px-4 py-3 text-left transition"
            :class="table.table_name === currentTable ? 'border-cyan-300 bg-cyan-50 shadow-sm shadow-cyan-100' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'"
            @click="selectTable(table.table_name)"
          >
            <div class="text-sm font-semibold text-slate-900">{{ table.label }}</div>
            <div class="mt-1 text-xs leading-5 text-slate-500">{{ table.description }}</div>
          </button>
        </div>
      </aside>

      <section class="rounded-[30px] border border-slate-200/80 bg-white/94 p-5 shadow-[0_30px_80px_rgba(15,23,42,0.10)]">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div class="text-[11px] uppercase tracking-[0.24em] text-slate-500">Table Workbench</div>
            <div class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{{ currentSchema?.label || '选择业务表' }}</div>
            <div class="mt-1 text-sm text-slate-500">{{ currentTable }}</div>
          </div>
          <div class="flex flex-wrap gap-3">
            <el-button @click="refreshCurrentTable">刷新</el-button>
            <el-button type="primary" @click="openCreateDialog">新增记录</el-button>
          </div>
        </div>

        <div class="mt-4 flex flex-wrap items-center gap-2">
          <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-500">{{ rows.length }} 行数据</span>
          <span v-if="lastMutationSummary" class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-700">{{ lastMutationSummary }}</span>
        </div>

        <el-table v-loading="loading" :data="rows" class="mt-5" stripe border height="620">
          <el-table-column
            v-for="field in visibleFields"
            :key="field.name"
            :prop="field.name"
            :label="field.label"
            min-width="140"
            show-overflow-tooltip
          />
          <el-table-column label="操作" fixed="right" width="150">
            <template #default="scope">
              <div class="flex gap-2">
                <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" plain @click="removeRow(scope.row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <aside class="rounded-[28px] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff_0%,#f7fbff_100%)] p-4 shadow-[0_22px_60px_rgba(15,23,42,0.08)]">
        <div class="flex items-center justify-between gap-3">
          <div class="text-[11px] uppercase tracking-[0.24em] text-violet-700/70">Recent Trigger Stream</div>
        </div>
        <div class="mt-3 max-h-[620px] space-y-3 overflow-y-auto pr-1">
          <div
            v-for="event in recentEvents"
            :key="event.change_event_id"
            class="w-full rounded-[22px] border border-slate-200 bg-white/90 p-3 text-left transition hover:border-violet-200 hover:bg-violet-50/40"
          >
            <div class="flex items-center justify-between gap-3">
              <div class="text-sm font-semibold text-slate-900">{{ event.table_name }}</div>
              <span class="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-[11px] text-violet-700">{{ event.operation }}</span>
            </div>
            <div class="mt-2 text-xs leading-5 text-slate-500">
              record_id: {{ event.record_id }}<br />
              event: {{ event.event_type }}<br />
              changed: {{ event.changed_fields.join(', ') || '-' }}
            </div>
            <div class="mt-2 text-xs text-emerald-700">触发 execution：{{ event.triggered_execution_ids.join(', ') || '无' }}</div>
          </div>
          <div v-if="recentEvents.length === 0" class="rounded-[22px] border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm text-slate-500">
            暂无最近触发事件。
          </div>
        </div>
      </aside>
    </div>

    <el-dialog v-model="editorVisible" width="640px" destroy-on-close align-center>
      <template #header>
        <div>
          <div class="text-[11px] uppercase tracking-[0.24em] text-cyan-700/80">Record Editor</div>
          <div class="mt-1 text-xl font-semibold text-slate-900">{{ editingMode === 'create' ? '新增记录' : '编辑记录' }}</div>
        </div>
      </template>

      <div class="grid gap-4 md:grid-cols-2">
        <div v-for="field in editableFields" :key="field.name">
          <div class="mb-1.5 text-[11px] uppercase tracking-[0.18em] text-slate-500">{{ field.label }}</div>
          <el-input-number
            v-if="field.field_type === 'number'"
            v-model="draftValues[field.name]"
            class="!w-full"
            :controls="false"
          />
          <el-input v-else v-model="draftValues[field.name]" />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="editorVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitEditor">保存并触发</el-button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import WorkspaceTopNav from '@/components/layout/WorkspaceTopNav.vue'
import {
  createRecordRow,
  deleteRecordRow,
  fetchRecentRecordEvents,
  fetchRecordRows,
  fetchRecordSources,
  fetchRecordTables,
  fetchRecordTableSchema,
  updateRecordRow,
} from '@/api/records'
import { useRecordsStore } from '@/store/records'
import type { RecordsTableSchemaField } from '@/types/records'

const recordsStore = useRecordsStore()
const loading = ref(false)
const saving = ref(false)
const editorVisible = ref(false)
const editingMode = ref<'create' | 'edit'>('create')
const editingRecordId = ref('')
const draftValues = reactive<Record<string, string | number>>({})
const tables = computed(() => recordsStore.tables)
const rows = computed(() => recordsStore.currentRows)
const currentTable = computed(() => recordsStore.currentTable)
const currentSchema = computed(() => recordsStore.currentSchema)
const recentEvents = computed(() => recordsStore.recentEvents)
const lastMutationSummary = computed(() => recordsStore.lastMutationSummary)
const currentSourceLabel = computed(() => recordsStore.sources[0]?.label ?? 'Mock Records 独立测试库')
const visibleFields = computed(() => currentSchema.value?.fields ?? [])
const editableFields = computed(() => visibleFields.value.filter((field) => field.editable))

const normalizeValueForField = (field: RecordsTableSchemaField, value: unknown) => {
  if (field.field_type === 'number') {
    return typeof value === 'number' ? value : Number(value ?? 0)
  }
  return typeof value === 'string' ? value : String(value ?? '')
}

const loadSourcesAndTables = async () => {
  const [sourcesResponse, tablesResponse] = await Promise.all([fetchRecordSources(), fetchRecordTables()])
  recordsStore.sources = sourcesResponse.data.sources
  recordsStore.tables = tablesResponse.data.tables
  if (!recordsStore.currentTable && recordsStore.tables[0]) {
    recordsStore.currentTable = recordsStore.tables[0].table_name
  }
}

const loadTableData = async (tableName: string) => {
  if (!tableName) return
  loading.value = true
  try {
    const [schemaResponse, rowsResponse, recentEventsResponse] = await Promise.all([
      fetchRecordTableSchema(tableName),
      fetchRecordRows(tableName),
      fetchRecentRecordEvents(),
    ])
    recordsStore.currentSchema = schemaResponse.data
    recordsStore.currentRows = rowsResponse.data.rows
    recordsStore.recentEvents = recentEventsResponse.data.events
    recordsStore.currentTable = tableName
  } finally {
    loading.value = false
  }
}

const refreshCurrentTable = async () => {
  await loadTableData(recordsStore.currentTable)
}

const selectTable = async (tableName: string) => {
  await loadTableData(tableName)
}

const openCreateDialog = () => {
  editingMode.value = 'create'
  editingRecordId.value = ''
  editableFields.value.forEach((field) => {
    draftValues[field.name] = field.field_type === 'number' ? 0 : ''
  })
  editorVisible.value = true
}

const openEditDialog = (row: Record<string, unknown>) => {
  editingMode.value = 'edit'
  editingRecordId.value = String(row.id ?? '')
  editableFields.value.forEach((field) => {
    draftValues[field.name] = normalizeValueForField(field, row[field.name])
  })
  editorVisible.value = true
}

const submitEditor = async () => {
  if (!recordsStore.currentTable) return
  saving.value = true
  try {
    const payload = editableFields.value.reduce<Record<string, unknown>>((accumulator, field) => {
      accumulator[field.name] = normalizeValueForField(field, draftValues[field.name])
      return accumulator
    }, {})
    const response = editingMode.value === 'create'
      ? await createRecordRow(recordsStore.currentTable, payload)
      : await updateRecordRow(recordsStore.currentTable, editingRecordId.value, payload)
    recordsStore.lastMutationSummary = `事件 ${response.data.change_event_id} 已触发，execution ${response.data.triggered_execution_ids.join(', ') || '无'}`
    editorVisible.value = false
    ElMessage.success('记录已保存并触发联调链路')
    await refreshCurrentTable()
  } finally {
    saving.value = false
  }
}

const removeRow = async (row: Record<string, unknown>) => {
  try {
    await ElMessageBox.confirm('删除后将直接触发数据库变更事件，确认继续？', '删除记录', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  const response = await deleteRecordRow(recordsStore.currentTable, String(row.id ?? ''))
  recordsStore.lastMutationSummary = `事件 ${response.data.change_event_id} 已触发，execution ${response.data.triggered_execution_ids.join(', ') || '无'}`
  ElMessage.success('记录已删除并触发联调链路')
  await refreshCurrentTable()
}

onMounted(async () => {
  await loadSourcesAndTables()
  if (recordsStore.currentTable) {
    await loadTableData(recordsStore.currentTable)
  }
})
</script>
