<template>
  <el-dialog
    :model-value="visible"
    width="980px"
    top="6vh"
    destroy-on-close
    align-center
    class="workflow-node-dialog"
    @close="closeDialog"
  >
    <template #header>
      <div class="flex items-start justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-[0.24em] text-sky-500/80">节点属性面板</div>
          <div class="mt-2 text-2xl font-semibold text-slate-900">{{ selectedNode?.label || '节点设置' }}</div>
        </div>
      </div>
    </template>

    <div v-if="!selectedNode" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center text-slate-500">
      当前没有选中的节点。
    </div>

    <div v-else class="space-y-5">
      <div class="rounded-[20px] border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] px-4 py-3 shadow-sm shadow-slate-200/60">
        <div class="flex flex-wrap items-start gap-3 xl:flex-nowrap xl:items-center">
          <div class="min-w-0 flex-1">
            <div class="mb-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">基础信息</div>
            <div class="grid gap-2 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <el-input v-model="label" placeholder="节点名称" @change="updateLabel" />
              <el-input v-model="description" placeholder="节点说明" @change="updateDescription" />
            </div>
          </div>

          <div class="flex flex-wrap gap-2 xl:justify-end">
            <div class="rounded-2xl border border-slate-200 bg-slate-50/90 px-3 py-2 text-sm text-slate-700">
              <span class="text-xs text-slate-500">节点类型</span>
              <div class="mt-1 font-medium text-slate-900">{{ nodeTypeLabel }}</div>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-slate-50/90 px-3 py-2 text-sm text-slate-700 max-w-[280px]">
              <span class="text-xs text-slate-500">节点 ID</span>
              <div class="mt-1 break-all font-medium text-slate-900">{{ selectedNode.id }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <div class="text-xs uppercase tracking-[0.2em] text-slate-500">主要设置</div>
        <div class="space-y-3">
            <template v-if="selectedNode.type === 'dialog_agent'">
              <DialogConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else-if="selectedNode.type === 'execution_agent'">
              <ExecutionConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else-if="selectedNode.type === 'decision_agent'">
              <DecisionConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else-if="selectedNode.type === 'sensor_agent'">
              <SensorConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else-if="selectedNode.type === 'condition'">
              <ConditionConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else-if="selectedNode.type === 'parallel'">
              <div class="rounded-[24px] border border-dashed border-cyan-300 bg-cyan-50 px-4 py-6 text-sm leading-6 text-cyan-900">
                并行控制节点当前采用最小配置口径：不需要专属表单，直接通过多条下游连线并列挂多个执行智能体即可。若需要进一步补 join / 超时 / 分支策略，再使用下方 JSON 高级配置补充字段。
              </div>
            </template>

            <template v-else-if="selectedNode.type === 'approval'">
              <ApprovalConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else-if="selectedNode.type === 'wait'">
              <WaitConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else-if="selectedNode.type === 'exception'">
              <ExceptionConfigPanel :model-value="selectedNode.config" @update:model-value="updateStructuredConfig" />
            </template>

            <template v-else>
              <div class="rounded-[24px] border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-sm text-slate-500">当前节点类型暂无专属表单，先使用左侧 JSON 高级配置。</div>
            </template>
        </div>
      </div>

      <div class="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm shadow-slate-200/70 space-y-3">
        <div class="text-xs uppercase tracking-[0.2em] text-slate-500">高级配置（JSON）</div>
        <el-input
          v-model="configText"
          type="textarea"
          :rows="11"
          placeholder='{"key":"value"}'
          @change="updateConfig"
        />
        <div class="text-xs leading-5 text-slate-500">保留给精细化调试与临时补充字段，主要设置优先使用上方结构化表单。</div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between">
        <div class="text-xs text-slate-500">保存节点名称、说明和专属表单配置后会立即同步到当前 workflow 草稿。</div>
        <div class="flex gap-3">
          <el-button @click="closeDialog">关闭</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import DecisionConfigPanel from '@/components/canvas/panels/DecisionConfigPanel.vue'
import DialogConfigPanel from '@/components/canvas/panels/DialogConfigPanel.vue'
import ExecutionConfigPanel from '@/components/canvas/panels/ExecutionConfigPanel.vue'
import ConditionConfigPanel from '@/components/canvas/panels/ConditionConfigPanel.vue'
import ApprovalConfigPanel from '@/components/canvas/panels/ApprovalConfigPanel.vue'
import WaitConfigPanel from '@/components/canvas/panels/WaitConfigPanel.vue'
import ExceptionConfigPanel from '@/components/canvas/panels/ExceptionConfigPanel.vue'
import SensorConfigPanel from '@/components/canvas/panels/SensorConfigPanel.vue'
import { useWorkflowStore } from '@/store/workflow'
import type {
  ApprovalNodeConfig,
  ConditionNodeConfig,
  DecisionNodeConfig,
  DialogNodeConfig,
  ExceptionNodeConfig,
  ExecutionNodeConfig,
  SensorNodeConfig,
  WaitNodeConfig,
} from '@/types/workflow'

const workflowStore = useWorkflowStore()
const selectedNode = computed(() => workflowStore.selectedNode)
const visible = computed(() => workflowStore.nodeConfigVisible)
const label = ref('')
const description = ref('')
const configText = ref('{}')
const nodeTypeLabelMap: Record<string, string> = {
  dialog_agent: '对话智能体',
  sensor_agent: '感知智能体',
  decision_agent: '决策智能体',
  execution_agent: '执行智能体',
  condition: '条件节点',
  parallel: '并行节点',
  approval: '审批节点',
  wait: '等待节点',
  exception: '异常节点',
}

const nodeTypeLabel = computed(() => (selectedNode.value ? nodeTypeLabelMap[selectedNode.value.type] ?? selectedNode.value.type : '未选择节点'))

watch(
  selectedNode,
  (node) => {
    label.value = node?.label ?? ''
    description.value = typeof node?.config?.description === 'string' ? node.config.description : ''
    configText.value = JSON.stringify(node?.config ?? {}, null, 2)
  },
  { immediate: true },
)

const updateLabel = () => {
  workflowStore.updateSelectedNodeLabel(label.value)
}

const updateConfig = () => {
  try {
    const parsed = JSON.parse(configText.value) as Record<string, unknown>
    workflowStore.updateSelectedNodeConfig(parsed)
  } catch {
    ElMessage.error('节点配置必须是合法 JSON')
  }
}

const updateDescription = () => {
  try {
    const parsed = JSON.parse(configText.value) as Record<string, unknown>
    parsed.description = description.value
    workflowStore.updateSelectedNodeConfig(parsed)
    configText.value = JSON.stringify(parsed, null, 2)
  } catch {
    workflowStore.updateSelectedNodeConfig({ description: description.value })
    configText.value = JSON.stringify({ description: description.value }, null, 2)
  }
}

type StructuredNodeConfig =
  | Record<string, unknown>
  | DialogNodeConfig
  | ExecutionNodeConfig
  | DecisionNodeConfig
  | SensorNodeConfig
  | ConditionNodeConfig
  | ApprovalNodeConfig
  | WaitNodeConfig
  | ExceptionNodeConfig

const updateStructuredConfig = (value: StructuredNodeConfig) => {
  const normalized = value as Record<string, unknown>
  workflowStore.updateSelectedNodeConfig(normalized)
  configText.value = JSON.stringify(normalized, null, 2)
  description.value = typeof normalized.description === 'string' ? normalized.description : ''
}

const closeDialog = () => {
  workflowStore.closeNodeConfig()
}
</script>

<style scoped>
:deep(.workflow-node-dialog) {
  --el-dialog-bg-color: #f8fbff;
  --el-text-color-primary: #0f172a;
  --el-border-color-lighter: rgba(203, 213, 225, 0.8);
  border-radius: 24px;
}

:deep(.workflow-node-dialog .el-dialog) {
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 28px;
  box-shadow: 0 32px 80px rgba(148, 163, 184, 0.22);
}

:deep(.workflow-node-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 24px 24px 8px;
}

:deep(.workflow-node-dialog .el-dialog__body) {
  padding: 8px 24px 8px;
}

:deep(.workflow-node-dialog .el-dialog__footer) {
  padding: 8px 24px 24px;
}
</style>
