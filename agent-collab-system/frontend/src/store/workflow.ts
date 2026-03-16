import { defineStore } from 'pinia'

import type { WorkflowCompileResult, WorkflowEdge, WorkflowNode, WorkflowSummary, WorkflowUiSchema } from '@/types/workflow'
import type { WorkflowCategoryValue } from '@/utils/workflowCategory'
import type { ErpDepartmentValue } from '@/utils/erpDepartments'

const generateDefaultWorkflowCode = () => `wf_canvas_${Date.now().toString(36)}`
const DEFAULT_WORKFLOW_NAME = '示例对话指令流'

const DEFAULT_NODES = [
  { type: 'dialog_agent', label: '对话入口' },
  { type: 'condition', label: '条件判断' },
  { type: 'execution_agent', label: '执行动作' },
]

export const useWorkflowStore = defineStore('workflow', {
  state: () => ({
    availableWorkflows: [] as WorkflowSummary[],
    currentWorkflowId: '' as string,
    workflowCode: '' as string,
    workflowName: DEFAULT_WORKFLOW_NAME as string,
    ownerDeptId: 'production' as ErpDepartmentValue,
    workflowCategory: 'dialog_trigger' as WorkflowCategoryValue,
    nodes: [] as WorkflowNode[],
    edges: [] as WorkflowEdge[],
    selectedNodeId: '' as string,
    selectedEdgeId: '' as string,
    nodePickerVisible: false,
    nodeConfigVisible: false,
    isDirty: false,
    compileStale: false,
    versions: [] as WorkflowCompileResult[],
    compileResult: null as WorkflowCompileResult | null,
    currentRelease: null as WorkflowCompileResult | null,
    activeAction: '' as '' | 'save' | 'compile' | 'publish' | 'load',
    activeExecutionId: '' as string,
    activeExecutionStatus: '' as string,
    activeRuntimeNodeId: '' as string,
  }),
  getters: {
    selectedNode(state): WorkflowNode | undefined {
      return state.nodes.find((node) => node.id === state.selectedNodeId)
    },
    isBusy(state): boolean {
      return state.activeAction !== ''
    },
    uiSchema(state): WorkflowUiSchema {
      return {
        nodes: state.nodes,
        edges: state.edges,
        viewport: { x: 0, y: 0, zoom: 1 },
      }
    },
  },
  actions: {
    setActiveAction(action: '' | 'save' | 'compile' | 'publish' | 'load') {
      this.activeAction = action
    },
    ensureDraftMeta() {
      if (!this.workflowCode) {
        this.workflowCode = generateDefaultWorkflowCode()
      }
      if (!this.workflowName) {
        this.workflowName = DEFAULT_WORKFLOW_NAME
      }
    },
    markDirty() {
      this.isDirty = true
      if (this.compileResult) {
        this.compileStale = true
      }
    },
    initializeDemoFlow() {
      const created = DEFAULT_NODES.map((item, index) => ({
        id: `node_${index + 1}`,
        type: item.type,
        label: item.label,
        config: {},
        position: { x: 120 + index * 260, y: 180 },
      }))
      this.nodes = created
      this.edges = [
        { id: 'edge_1', source: created[0].id, target: created[1].id },
        { id: 'edge_2', source: created[1].id, target: created[2].id },
      ]
      this.selectedNodeId = created[0].id
      this.selectedEdgeId = ''
      this.isDirty = true
      this.compileStale = true
    },
    resetWorkflowEditor() {
      this.nodes = []
      this.edges = []
      this.currentWorkflowId = ''
      this.workflowCode = ''
      this.workflowName = DEFAULT_WORKFLOW_NAME
      this.ownerDeptId = 'production'
      this.workflowCategory = 'dialog_trigger'
      this.selectedNodeId = ''
      this.selectedEdgeId = ''
      this.nodePickerVisible = false
      this.nodeConfigVisible = false
      this.isDirty = false
      this.compileStale = false
      this.compileResult = null
      this.currentRelease = null
      this.versions = []
      this.activeExecutionId = ''
      this.activeExecutionStatus = ''
      this.activeRuntimeNodeId = ''
    },
    addNode(type: string, label?: string) {
      const id = `node_${Date.now()}_${this.nodes.length + 1}`
      this.nodes.push({
        id,
        type,
        label: label || type,
        config: {},
        position: {
          x: 160 + (this.nodes.length % 3) * 260,
          y: 120 + Math.floor(this.nodes.length / 3) * 180,
        },
      })
      if (!this.selectedNodeId) {
        this.selectedNodeId = id
      }
      this.selectedNodeId = id
      this.nodeConfigVisible = true
      this.markDirty()
    },
    addEdge(source: string, target: string) {
      if (!source || !target || source === target) {
        return
      }
      const exists = this.edges.some((edge) => edge.source === source && edge.target === target)
      if (exists) {
        return
      }
      this.edges.push({
        id: `edge_${Date.now()}_${this.edges.length + 1}`,
        source,
        target,
      })
      this.markDirty()
    },
    selectNode(nodeId: string) {
      this.selectedNodeId = nodeId
      this.selectedEdgeId = ''
      this.nodeConfigVisible = true
    },
    openNodePicker() {
      this.nodePickerVisible = true
    },
    closeNodePicker() {
      this.nodePickerVisible = false
    },
    selectEdge(edgeId: string) {
      this.selectedEdgeId = edgeId
      this.selectedNodeId = ''
      this.nodeConfigVisible = false
    },
    closeNodeConfig() {
      this.nodeConfigVisible = false
    },
    updateSelectedNodeLabel(label: string) {
      const node = this.nodes.find((item) => item.id === this.selectedNodeId)
      if (node) {
        node.label = label
        this.markDirty()
      }
    },
    updateSelectedNodeConfig(config: Record<string, unknown>) {
      const node = this.nodes.find((item) => item.id === this.selectedNodeId)
      if (node) {
        node.config = config
        this.markDirty()
      }
    },
    updateNodePosition(nodeId: string, position: { x: number; y: number }) {
      const node = this.nodes.find((item) => item.id === nodeId)
      if (node) {
        node.position = position
        this.markDirty()
      }
    },
    deleteSelectedNode() {
      if (!this.selectedNodeId) {
        return
      }
      const nodeId = this.selectedNodeId
      this.nodes = this.nodes.filter((node) => node.id !== nodeId)
      this.edges = this.edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
      this.selectedNodeId = ''
      this.nodeConfigVisible = false
      this.markDirty()
    },
    deleteNodeById(nodeId: string) {
      if (!nodeId) {
        return
      }
      this.nodes = this.nodes.filter((node) => node.id !== nodeId)
      this.edges = this.edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
      if (this.selectedNodeId === nodeId) {
        this.selectedNodeId = ''
        this.nodeConfigVisible = false
      }
      this.markDirty()
    },
    deleteSelectedEdge() {
      if (!this.selectedEdgeId) {
        return
      }
      this.edges = this.edges.filter((edge) => edge.id !== this.selectedEdgeId)
      this.selectedEdgeId = ''
      this.markDirty()
    },
    deleteEdgeById(edgeId: string) {
      if (!edgeId) {
        return
      }
      this.edges = this.edges.filter((edge) => edge.id !== edgeId)
      if (this.selectedEdgeId === edgeId) {
        this.selectedEdgeId = ''
      }
      this.markDirty()
    },
    loadWorkflow(payload: {
      summary: WorkflowSummary
      draft: WorkflowCompileResult
      release: WorkflowCompileResult | null
      versions: WorkflowCompileResult[]
    }) {
      this.currentWorkflowId = payload.summary.workflow_id
      this.workflowCode = payload.summary.code
      this.workflowName = payload.summary.name
      this.ownerDeptId = payload.summary.owner_dept_id as ErpDepartmentValue
      this.workflowCategory = (payload.summary.workflow_trigger_type as WorkflowCategoryValue) || 'dialog_trigger'
      const clonedNodes = structuredClone(payload.draft.ui_schema.nodes)
      const clonedEdges = structuredClone(payload.draft.ui_schema.edges)
      const draftSnapshot = structuredClone(payload.draft)
      const releaseSnapshot = payload.release ? structuredClone(payload.release) : null
      const versionSnapshots = structuredClone(payload.versions)
      this.nodes = clonedNodes
      this.edges = clonedEdges
      this.selectedNodeId = clonedNodes[0]?.id ?? ''
      this.selectedEdgeId = ''
      this.nodeConfigVisible = false
      this.isDirty = false
      this.compileStale = false
      this.compileResult = draftSnapshot
      this.currentRelease = releaseSnapshot
      this.versions = versionSnapshots
      this.activeExecutionId = ''
      this.activeExecutionStatus = ''
      this.activeRuntimeNodeId = ''
    },
    setWorkflowMeta(payload: { name?: string; code?: string; workflowId?: string; workflowCategory?: WorkflowCategoryValue; ownerDeptId?: ErpDepartmentValue }) {
      if (payload.name !== undefined) {
        this.workflowName = payload.name
        this.markDirty()
      }
      if (payload.code !== undefined) {
        this.workflowCode = payload.code
        this.markDirty()
      }
      if (payload.workflowId !== undefined) {
        this.currentWorkflowId = payload.workflowId
      }
      if (payload.workflowCategory !== undefined) {
        this.workflowCategory = payload.workflowCategory
        this.markDirty()
      }
      if (payload.ownerDeptId !== undefined) {
        this.ownerDeptId = payload.ownerDeptId
        this.markDirty()
      }
    },
    setVersions(versions: WorkflowCompileResult[]) {
      this.versions = versions
    },
    setCompileResult(result: WorkflowCompileResult | null) {
      this.compileResult = result
      this.compileStale = false
      this.isDirty = false
    },
    setDraftSnapshot(result: WorkflowCompileResult | null) {
      this.compileResult = result
      this.isDirty = false
      this.compileStale = true
    },
    setCurrentRelease(result: WorkflowCompileResult | null) {
      this.currentRelease = result
    },
    setAvailableWorkflows(workflows: WorkflowSummary[]) {
      this.availableWorkflows = workflows
    },
    setRuntimeExecution(payload: { executionId?: string; status?: string; currentNode?: string | null }) {
      this.activeExecutionId = payload.executionId ?? ''
      this.activeExecutionStatus = payload.status ?? ''
      this.activeRuntimeNodeId = payload.currentNode ?? ''
    },
    clearRuntimeExecution() {
      this.activeExecutionId = ''
      this.activeExecutionStatus = ''
      this.activeRuntimeNodeId = ''
    },
  },
})
