<template>
  <div
    ref="canvasShellRef"
    class="rounded-[30px] border border-slate-200/90 bg-white/95 p-4 shadow-[0_28px_80px_rgba(15,23,42,0.10)] backdrop-blur"
    :class="isFullscreen ? 'fixed inset-4 z-[1200] p-5' : 'min-h-[760px]'"
  >
    <div class="mb-4 flex flex-wrap items-start justify-between gap-4 rounded-[24px] border border-slate-200 bg-[linear-gradient(135deg,#ffffff_0%,#f8fbff_52%,#eef4ff_100%)] px-5 py-4 shadow-[0_18px_50px_rgba(148,163,184,0.18)]">
      <div class="space-y-2">
        <div class="text-[11px] uppercase tracking-[0.32em] text-sky-700/70">工作流编辑区</div>
        <div>
          <div class="text-xl font-semibold tracking-tight text-slate-950">全屏画布编辑区</div>
          <div class="mt-1 text-sm text-slate-500">拖拽节点、直接连线，点击节点后在画布内弹出配置面板。</div>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <div class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-500">
          {{ nodes.length }} 个节点 · {{ edges.length }} 条连线
        </div>
        <div
          v-if="activeExecutionId"
          class="rounded-full border px-3 py-1.5 text-xs font-medium"
          :class="activeExecutionStatus === 'running'
            ? 'border-fuchsia-200 bg-fuchsia-50 text-fuchsia-700 shadow-[0_0_24px_rgba(217,70,239,0.16)]'
            : 'border-slate-200 bg-white text-slate-500'"
        >
          {{ runtimeStatusLabel }}
        </div>
        <el-button plain @click="resetCanvas">初始化示例流程</el-button>
        <el-button plain type="danger" :disabled="!selectedNodeId" @click="deleteSelectedNode">删除节点</el-button>
        <el-button plain type="danger" :disabled="!selectedEdgeId" @click="deleteSelectedEdge">删除连线</el-button>
        <el-button type="primary" @click="toggleFullscreen">
          {{ isFullscreen ? '退出全屏' : '全屏编辑' }}
        </el-button>
      </div>
    </div>

    <div class="relative rounded-[26px] border border-slate-200 bg-[linear-gradient(180deg,#f8fbff_0%,#f2f6fb_100%)] p-3 shadow-inner shadow-slate-100/60">
      <div class="relative overflow-hidden rounded-[22px] border border-slate-200/80 bg-slate-50/90 p-2">
        <VueFlow
          :nodes="flowNodes"
          :edges="flowEdges"
          :node-types="nodeTypes"
          :edge-types="edgeTypes"
          class="rounded-[18px] bg-[radial-gradient(circle_at_1px_1px,rgba(148,163,184,0.25)_1px,transparent_0)] [background-size:24px_24px]"
          :class="isFullscreen ? 'h-[calc(100vh-220px)]' : 'h-[700px]'"
          :min-zoom="0.4"
          :max-zoom="1.6"
          fit-view-on-init
          @connect="handleConnect"
          @node-click="handleNodeClick"
          @edge-click="handleEdgeClick"
          @node-drag-stop="handleNodeDragStop"
        />

        <button
          class="absolute right-5 top-5 z-20 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-sky-500 via-indigo-500 to-violet-500 text-2xl font-semibold text-white shadow-[0_18px_35px_rgba(79,70,229,0.35)] transition duration-200 hover:scale-[1.04]"
          @click="openNodePicker"
        >
          +
        </button>

        <div class="absolute left-5 top-5 z-20 flex flex-wrap items-center gap-2">
          <div class="rounded-full border border-white/70 bg-white/88 px-3 py-1 text-xs text-slate-500 backdrop-blur">
            智能排产流程图
          </div>
          <div class="rounded-full border border-sky-200/80 bg-sky-50/90 px-3 py-1 text-xs font-medium text-sky-700 backdrop-blur">
            {{ isFullscreen ? '沉浸编辑中' : '标准编辑视图' }}
          </div>
        </div>

        <div class="absolute bottom-5 left-5 z-20 flex flex-col gap-2 rounded-[20px] border border-slate-200/90 bg-white/88 p-2 shadow-[0_18px_30px_rgba(15,23,42,0.12)] backdrop-blur">
          <button class="h-11 w-11 rounded-2xl border border-slate-200 bg-white text-xl text-slate-700 transition hover:bg-slate-50" @click="zoomInCanvas">+</button>
          <button class="h-11 w-11 rounded-2xl border border-slate-200 bg-white text-xl text-slate-700 transition hover:bg-slate-50" @click="zoomOutCanvas">−</button>
          <button class="h-11 w-11 rounded-2xl border border-slate-200 bg-white text-base text-slate-700 transition hover:bg-slate-50" @click="fitCanvas">⌖</button>
        </div>

        <NodePalette />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { VueFlow, useVueFlow, type Connection, type NodeMouseEvent, type NodeDragEvent, type EdgeMouseEvent, type Edge as FlowEdge, type Node as FlowNode, MarkerType } from '@vue-flow/core'

import { useWorkflowCanvas } from '@/composables/useWorkflowCanvas'
import WorkflowGraphEdge from '@/components/canvas/edges/WorkflowGraphEdge.vue'
import NodePalette from '@/components/canvas/NodePalette.vue'
import WorkflowGraphNode from '@/components/canvas/nodes/WorkflowGraphNode.vue'
import { useWorkflowStore } from '@/store/workflow'

const nodeTypes = {
  workflow: markRaw(WorkflowGraphNode),
}

const edgeTypes = {
  workflow: markRaw(WorkflowGraphEdge),
}

const canvasShellRef = ref<HTMLElement | null>(null)
const isFullscreen = ref(false)
const workflowStore = useWorkflowStore()
const { fitView, zoomIn, zoomOut } = useVueFlow()
const { nodes, edges, selectNode, updateNodePosition } = useWorkflowCanvas()

const typeLabels: Record<string, string> = {
  dialog_agent: '对话',
  sensor_agent: '感知',
  decision_agent: '决策',
  execution_agent: '执行',
  condition: '条件',
  approval: '审批',
  wait: '等待',
  exception: '异常',
}

const flowNodes = computed<FlowNode[]>(() =>
  nodes.value.map((node) => ({
    id: node.id,
    type: 'workflow',
    position: node.position ?? { x: 120, y: 160 },
      data: {
        label: node.label,
        type: node.type,
        typeLabel: typeLabels[node.type] ?? node.type,
        description: resolveNodeDescription(node),
        isExecuting: workflowStore.activeRuntimeNodeId === node.id && workflowStore.activeExecutionStatus === 'running',
      },
    })),
)

const resolveNodeDescription = (node: { type: string; config: Record<string, unknown> }) => {
  if (typeof node.config.description === 'string' && node.config.description.trim()) {
    return node.config.description
  }

  if (node.type === 'sensor_agent') {
    const sourceSystem = typeof node.config.source_system === 'string' ? node.config.source_system : ''
    const sourceTable = typeof node.config.source_table === 'string' ? node.config.source_table : ''
    const sourceEventKey = typeof node.config.source_event_key === 'string' ? node.config.source_event_key : ''
    const summary = [sourceSystem, sourceTable, sourceEventKey].filter(Boolean).join(' · ')
    return summary || '监听数据库/业务事件后触发后续节点'
  }

  if (node.type === 'execution_agent') {
    const target = Array.isArray(node.config.execution_targets)
      ? (node.config.execution_targets[0] as Record<string, unknown> | undefined)
      : undefined
    const targetRef = typeof target?.target_ref === 'string' ? target.target_ref : '未配置目标'
    const operation = typeof target?.operation === 'string' ? target.operation : 'append_row'
    return `${operation} · ${targetRef}`
  }

  return '点击节点后弹出配置界面'
}

const flowEdges = computed<FlowEdge[]>(() =>
  edges.value.map((edge) => ({
    id: edge.id,
    type: 'workflow',
    source: edge.source,
    target: edge.target,
    label: edge.label,
    markerEnd: MarkerType.ArrowClosed,
    style: { stroke: '#38bdf8', strokeWidth: 2 },
    labelStyle: { fill: '#cbd5e1', fontSize: 12 },
  })),
)

const handleNodeClick = (event: NodeMouseEvent) => {
  selectNode(String(event.node.id))
}

const selectedNodeId = computed(() => workflowStore.selectedNodeId)
const selectedEdgeId = computed(() => workflowStore.selectedEdgeId)
const activeExecutionId = computed(() => workflowStore.activeExecutionId)
const activeRuntimeNode = computed(() => nodes.value.find((node) => node.id === workflowStore.activeRuntimeNodeId))
const activeExecutionStatus = computed(() => workflowStore.activeExecutionStatus)
const runtimeStatusLabel = computed(() => {
  if (!activeExecutionId.value) {
    return ''
  }
  if (activeExecutionStatus.value === 'running') {
    return `运行中 · ${activeRuntimeNode.value?.label || workflowStore.activeRuntimeNodeId || '等待节点状态'}`
  }
  if (activeExecutionStatus.value === 'waiting_approval') {
    return `等待审批 · ${activeRuntimeNode.value?.label || workflowStore.activeRuntimeNodeId || '审批节点'}`
  }
  if (activeExecutionStatus.value === 'finished') {
    return '最近一次运行已完成'
  }
  if (activeExecutionStatus.value === 'failed') {
    return '最近一次运行失败'
  }
  return `执行状态 · ${activeExecutionStatus.value}`
})

const handleEdgeClick = (event: EdgeMouseEvent) => {
  workflowStore.selectEdge(String(event.edge.id))
}

const handleNodeDragStop = (event: NodeDragEvent) => {
  updateNodePosition(String(event.node.id), {
    x: event.node.position.x,
    y: event.node.position.y,
  })
}

const handleConnect = (connection: Connection) => {
  if (connection.source && connection.target) {
    workflowStore.addEdge(connection.source, connection.target)
  }
}

const fitCanvas = async () => {
  await fitView({ padding: 0.16, duration: 400 })
}

const zoomInCanvas = async () => {
  await zoomIn({ duration: 200 })
}

const zoomOutCanvas = async () => {
  await zoomOut({ duration: 200 })
}

const openNodePicker = () => {
  workflowStore.openNodePicker()
}

const syncFullscreenState = () => {
  isFullscreen.value = document.fullscreenElement === canvasShellRef.value
}

const toggleFullscreen = async () => {
  if (!canvasShellRef.value) {
    return
  }

  if (document.fullscreenElement === canvasShellRef.value) {
    await document.exitFullscreen()
    return
  }

  await canvasShellRef.value.requestFullscreen()
}

const resetCanvas = () => {
  const executeReset = () => {
    workflowStore.resetWorkflowEditor()
    workflowStore.initializeDemoFlow()
  }

  if (workflowStore.isDirty) {
    ElMessageBox.confirm('当前画布存在未保存修改，重置后会丢失。是否继续？', '未保存提醒', {
      confirmButtonText: '继续重置',
      cancelButtonText: '取消',
      type: 'warning',
    })
      .then(executeReset)
      .catch(() => undefined)
    return
  }

  executeReset()
}

const deleteSelectedNode = () => {
  workflowStore.deleteSelectedNode()
}

const deleteSelectedEdge = () => {
  workflowStore.deleteSelectedEdge()
}

onMounted(() => {
  document.addEventListener('fullscreenchange', syncFullscreenState)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState)
})
</script>
