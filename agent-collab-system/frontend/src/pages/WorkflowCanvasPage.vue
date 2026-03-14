<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#edf3fb_0%,#f8fbff_44%,#eef2f7_100%)] px-4 py-5 text-slate-900 md:px-6">
    <div>
      <WorkspaceTopNav
        title="工作流制作区"
        description="面向流程配置员维护 workflow 画布、节点配置、草稿编译与发布。"
      />

      <div class="mb-4 overflow-hidden rounded-[28px] border border-slate-200/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(248,250,252,0.98))] shadow-[0_24px_64px_rgba(15,23,42,0.08)]">
        <div class="border-b border-slate-200/80 px-5 py-3 md:px-6">
          <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div class="space-y-1.5">
              <div class="text-[11px] uppercase tracking-[0.34em] text-sky-700/70">工作流画布工作台</div>
              <div>
                <div class="text-[24px] font-semibold tracking-tight text-slate-950">{{ workflowNameProxy || '未命名工作流' }}</div>
                <div class="mt-0.5 text-[13px] text-slate-500">面向配置员的沉浸式画布编辑区，顶部只保留必要元信息与核心动作。</div>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-1.5 xl:justify-end">
              <div class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">{{ nodeCount }} 个节点</div>
              <div class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">{{ edgeCount }} 条连线</div>
              <div class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                {{ compileStatusLabel }}
              </div>
              <div class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500">发布版本 {{ releaseLabel }}</div>
            </div>
          </div>
        </div>

        <div class="grid gap-3 px-5 py-4 md:grid-cols-2 md:px-6 xl:grid-cols-5">
          <div class="min-w-0">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">工作流名称</div>
            <div class="rounded-[20px] border border-slate-200 bg-slate-50/80 p-1.5 shadow-inner shadow-white/70">
              <el-input v-model="workflowNameProxy" placeholder="工作流名称" />
            </div>
          </div>

          <div class="min-w-0">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">工作流编码</div>
            <div class="rounded-[20px] border border-slate-200 bg-slate-50/80 p-1.5 shadow-inner shadow-white/70">
              <el-input v-model="workflowCodeProxy" placeholder="工作流编码" />
            </div>
          </div>

          <div class="rounded-[20px] border border-slate-200 bg-slate-50/80 px-3.5 py-2.5 text-sm text-slate-600 shadow-inner shadow-white/60">
            <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">流程编号</div>
            <div class="mt-1 truncate font-medium text-slate-900">{{ workflowId || '尚未创建' }}</div>
          </div>

          <div class="min-w-0">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">工作流分类</div>
            <div class="rounded-[20px] border border-slate-200 bg-slate-50/80 p-1.5 shadow-inner shadow-white/70">
              <el-select v-model="workflowCategoryProxy" class="w-full" placeholder="选择工作流分类">
                <el-option v-for="item in WORKFLOW_TRIGGER_TYPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </div>

          <div class="min-w-0 xl:min-w-[220px]">
            <div class="mb-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">加载已有流程</div>
            <div class="rounded-[20px] border border-slate-200 bg-slate-50/80 p-1.5 shadow-inner shadow-white/70">
              <el-select v-model="selectedWorkflowToLoad" class="w-full" placeholder="选择已有流程" @change="handleLoadWorkflow">
                <el-option
                  v-for="item in availableWorkflows"
                  :key="item.workflow_id"
                  :label="`${item.name} (${item.code})`"
                  :value="item.workflow_id"
                />
              </el-select>
            </div>
          </div>

          <div class="md:col-span-2 xl:col-span-5 flex flex-wrap items-end gap-1.5">
            <el-button @click="saveDraft">保存草稿</el-button>
            <el-button @click="compile">编译</el-button>
            <el-button type="success" :disabled="!canPublish" @click="publish">发布</el-button>
            <el-button plain :disabled="!canInjectMockEvent" @click="openMockEventDialog">模拟感知事件</el-button>
            <el-button type="danger" plain :disabled="!workflowId" @click="handleDeleteWorkflow">删除工作流</el-button>
          </div>
        </div>

        <div v-if="workflowStore.compileStale || compileErrors.length > 0" class="mx-5 mb-5 rounded-[22px] border border-amber-200 bg-[linear-gradient(135deg,#fff8eb,#fff3d6)] px-4 py-3 text-sm text-amber-900 md:mx-6">
          <div class="font-medium">发布前检查</div>
          <div v-if="workflowStore.compileStale" class="mt-2">当前画布自上次编译后已发生修改，请重新编译后再发布。</div>
          <ul v-if="compileErrors.length > 0" class="mt-2 list-disc pl-5 space-y-1">
            <li v-for="(error, index) in compileErrors" :key="index">
              {{ String(error.code ?? 'COMPILE_ERROR') }}：{{ String(error.message ?? '编译失败') }}
            </li>
          </ul>
        </div>
      </div>

      <WorkflowCanvas />

      <NodeConfigPanel />

      <el-dialog v-model="mockEventDialogVisible" width="640px" align-center destroy-on-close>
        <template #header>
          <div>
            <div class="text-[11px] uppercase tracking-[0.26em] text-cyan-600/80">感知型智能体验证</div>
            <div class="mt-1 text-xl font-semibold text-slate-900">模拟数据库事件注入</div>
            <div class="mt-1 text-sm text-slate-500">用标准事件信封触发当前 workflow，验证 sensor_agent 的来源匹配、条件命中与后续链路。</div>
          </div>
        </template>

        <div class="space-y-4">
          <div class="grid gap-3 md:grid-cols-2">
            <div>
              <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">事件类型</div>
              <el-input v-model="mockEventType" placeholder="record.updated" />
            </div>
            <div>
              <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">来源</div>
              <el-input v-model="mockSource" placeholder="go.records.gateway" />
            </div>
            <div>
              <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">来源系统</div>
              <el-input v-model="mockSourceSystem" placeholder="ERP生产库" />
            </div>
            <div>
              <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">数据表</div>
              <el-input v-model="mockTable" placeholder="inventory_stock" />
            </div>
          </div>

          <div>
            <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">变更操作</div>
            <el-input v-model="mockOperation" placeholder="updated" />
          </div>

          <div>
            <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">变更字段</div>
            <el-input v-model="mockChangedFieldsText" placeholder="stock_count,updated_at" />
          </div>

          <div>
            <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">after 快照 JSON</div>
            <el-input v-model="mockAfterJson" type="textarea" :rows="7" placeholder='{"item_id":"A-1001","stock_count":16,"safety_limit":20,"warehouse_id":"W-01"}' />
          </div>

          <div>
            <div class="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">before 快照 JSON（可选）</div>
            <el-input v-model="mockBeforeJson" type="textarea" :rows="5" placeholder='{"item_id":"A-1001","stock_count":18,"safety_limit":20,"warehouse_id":"W-01"}' />
          </div>

          <div v-if="latestMockExecution" class="rounded-[18px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            最近一次注入已创建执行：{{ latestMockExecution }}
          </div>
        </div>

        <template #footer>
          <div class="flex items-center justify-between gap-3">
            <div class="text-xs text-slate-500">优先使用已发布版本；若尚未发布，则回落到当前已编译草稿版本进行验证。</div>
            <div class="flex gap-3">
              <el-button @click="mockEventDialogVisible = false">关闭</el-button>
              <el-button type="primary" :loading="mockInjecting" @click="submitMockEvent">注入并运行</el-button>
            </div>
          </div>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import WorkflowCanvas from '@/components/canvas/WorkflowCanvas.vue'
import WorkspaceTopNav from '@/components/layout/WorkspaceTopNav.vue'
import NodeConfigPanel from '@/components/canvas/NodeConfigPanel.vue'
import { useWorkflowPublish } from '@/composables/useWorkflowPublish'
import { injectMockEvent } from '@/api/executions'
import { useWorkflowStore } from '@/store/workflow'
import { WORKFLOW_TRIGGER_TYPE_OPTIONS } from '@/utils/workflowCategory'

import { ElMessageBox } from 'element-plus'

const workflowStore = useWorkflowStore()

const selectedWorkflowToLoad = ref('')
const mockEventDialogVisible = ref(false)
const mockInjecting = ref(false)
const mockEventType = ref('record.updated')
const mockSource = ref('go.records.gateway')
const mockSourceSystem = ref('ERP生产库')
const mockTable = ref('inventory_stock')
const mockOperation = ref('updated')
const mockChangedFieldsText = ref('stock_count,updated_at')
const mockAfterJson = ref('{\n  "item_id": "A-1001",\n  "stock_count": 16,\n  "safety_limit": 20,\n  "warehouse_id": "W-01"\n}')
const mockBeforeJson = ref('{\n  "item_id": "A-1001",\n  "stock_count": 18,\n  "safety_limit": 20,\n  "warehouse_id": "W-01"\n}')
const latestMockExecution = ref('')

const workflowNameProxy = computed({
  get: () => workflowStore.workflowName,
  set: (value: string) => {
    workflowStore.setWorkflowMeta({ name: value })
  },
})

const workflowCodeProxy = computed({
  get: () => workflowStore.workflowCode,
  set: (value: string) => {
    workflowStore.setWorkflowMeta({ code: value })
  },
})

const workflowCategoryProxy = computed({
  get: () => workflowStore.workflowCategory,
  set: (value: string) => {
    workflowStore.setWorkflowMeta({ workflowCategory: value as typeof workflowStore.workflowCategory })
  },
})

const { canPublish, saveDraft, compile, publish, refreshWorkflowList, loadWorkflow, removeWorkflow } = useWorkflowPublish()

onMounted(async () => {
  workflowStore.ensureDraftMeta()
  await refreshWorkflowList()
})

const compileResult = computed(() => workflowStore.compileResult)
const currentRelease = computed(() => workflowStore.currentRelease)
const workflowId = computed(() => workflowStore.currentWorkflowId)
const compileStatusLabel = computed(() => {
  const status = compileResult.value?.compile_status
  if (status === 'success') {
    return '编译成功'
  }
  if (status === 'failed') {
    return '编译失败'
  }
  if (status === 'pending') {
    return '待编译'
  }
  return '未编译'
})
const releaseLabel = computed(() => currentRelease.value?.version ? `第 ${currentRelease.value.version} 版` : '未发布')
const nodeCount = computed(() => workflowStore.nodes.length)
const edgeCount = computed(() => workflowStore.edges.length)
const availableWorkflows = computed(() => workflowStore.availableWorkflows)
const compileErrors = computed(() => workflowStore.compileResult?.compile_errors ?? [])
const showSensorSandbox = computed(() => workflowStore.nodes.some((node) => node.type === 'sensor_agent'))
const canInjectMockEvent = computed(() => {
  if (!showSensorSandbox.value || !workflowId.value) {
    return false
  }
  if (currentRelease.value?.version) {
    return true
  }
  return compileResult.value?.compile_status === 'success' && !workflowStore.compileStale
})

const openMockEventDialog = () => {
  const sensorNode = workflowStore.nodes.find((node) => node.type === 'sensor_agent')
  const config = (sensorNode?.config ?? {}) as Record<string, unknown>
  if (typeof config.source_system === 'string' && config.source_system) {
    mockSourceSystem.value = config.source_system
  }
  if (typeof config.source_table === 'string' && config.source_table) {
    mockTable.value = config.source_table
  }
  if (typeof config.source_event_key === 'string' && config.source_event_key) {
    mockEventType.value = config.source_event_key
  }
  mockEventDialogVisible.value = true
}

const parseJsonInput = (raw: string, fieldName: string) => {
  if (!raw.trim()) {
    return undefined
  }
  try {
    return JSON.parse(raw) as Record<string, unknown>
  } catch {
    throw new Error(`${fieldName} 必须是合法 JSON`)
  }
}

const submitMockEvent = async () => {
  if (!workflowId.value) {
    ElMessage.warning('请先保存当前 workflow，再进行感知事件验证。')
    return
  }
  if (!canInjectMockEvent.value) {
    ElMessage.warning('请先保证当前 workflow 已发布，或草稿已编译成功且没有新的未编译修改。')
    return
  }

  mockInjecting.value = true
  try {
    const after = parseJsonInput(mockAfterJson.value, 'after 快照')
    const before = parseJsonInput(mockBeforeJson.value, 'before 快照')
    const changedFields = mockChangedFieldsText.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)

    const response = await injectMockEvent({
      workflow_id: workflowId.value,
      version: currentRelease.value?.version ?? compileResult.value?.version,
      mode: currentRelease.value ? 'released' : 'draft',
      event_type: mockEventType.value,
      source: mockSource.value,
      event: {
        source_system: mockSourceSystem.value,
        table: mockTable.value,
        operation: mockOperation.value,
        changed_fields: changedFields,
        ...(before ? { before } : {}),
        ...(after ? { after } : {}),
      },
    })

    latestMockExecution.value = `${response.data.execution_id} · ${response.data.status}`
    ElMessage.success('模拟感知事件已注入，感知链路开始执行。')
    mockEventDialogVisible.value = false
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : `注入失败：${String(error)}`)
  } finally {
    mockInjecting.value = false
  }
}

const handleLoadWorkflow = async (workflowIdToLoad: string) => {
  if (!workflowIdToLoad) {
    return
  }
  if (workflowStore.isDirty) {
    try {
      await ElMessageBox.confirm('当前 workflow 存在未保存修改，继续加载会覆盖当前画布。是否继续？', '未保存提醒', {
        confirmButtonText: '继续加载',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      selectedWorkflowToLoad.value = workflowStore.currentWorkflowId
      return
    }
  }
  await loadWorkflow(workflowIdToLoad)
}

const handleDeleteWorkflow = async () => {
  if (!workflowId.value) {
    return
  }
  try {
    await ElMessageBox.confirm('删除后该工作流会从制作区与查看区隐藏，确认继续？', '删除工作流', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await removeWorkflow(workflowId.value)
  selectedWorkflowToLoad.value = ''
}
</script>
