<template>
  <transition name="fade-slide">
    <div
      v-if="visible"
      class="absolute right-4 top-20 z-20 w-[320px] rounded-[24px] border border-slate-200 bg-white shadow-2xl shadow-slate-300/40"
    >
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div>
          <div class="text-lg font-semibold text-slate-900">节点面板</div>
          <div class="mt-1 text-sm text-slate-500">从这里选择节点加入当前工作流画布。</div>
        </div>
        <button class="text-xl text-slate-500 hover:text-slate-900" @click="closePicker">×</button>
      </div>

      <div class="px-4 py-4">
        <div class="mb-4 flex rounded-xl bg-slate-100 p-1 text-sm">
          <button
            class="flex-1 rounded-lg px-3 py-2 transition"
            :class="activeTab === 'agents' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500'"
            @click="activeTab = 'agents'"
          >
            智能体节点
          </button>
          <button
            class="flex-1 rounded-lg px-3 py-2 transition"
            :class="activeTab === 'controls' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500'"
            @click="activeTab = 'controls'"
          >
            流程控制
          </button>
        </div>

        <div class="space-y-3">
          <button
            v-for="node in displayedNodes"
            :key="node.type"
            class="w-full rounded-2xl border px-4 py-3 text-left transition hover:-translate-y-0.5"
            :class="node.className"
            @click="addNode(node.type, node.label)"
          >
            <div class="font-medium">{{ node.label }}</div>
            <div class="mt-1 text-xs opacity-80">{{ node.description }}</div>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { useWorkflowStore } from '@/store/workflow'
import type { WorkflowNodeType } from '@/types/workflow'

const workflowStore = useWorkflowStore()
const visible = computed(() => workflowStore.nodePickerVisible)
const activeTab = ref<'agents' | 'controls'>('agents')

const agentNodes: Array<{ type: WorkflowNodeType; label: string; description: string; className: string }> = [
  { type: 'sensor_agent', label: '感知智能体', description: '采集事件源 / 监听数据库变化', className: 'border-cyan-300 bg-cyan-50 text-cyan-950' },
  { type: 'decision_agent', label: '决策智能体', description: '规则 / 模型 / 智能决策', className: 'border-violet-300 bg-violet-50 text-violet-950' },
  { type: 'execution_agent', label: '执行智能体', description: '执行 API / 表格 / 外部动作', className: 'border-rose-300 bg-rose-50 text-rose-950' },
  { type: 'dialog_agent', label: '对话智能体', description: '人机交互 / 命令汇总', className: 'border-indigo-300 bg-indigo-50 text-indigo-950' },
]

const controlNodes: Array<{ type: WorkflowNodeType; label: string; description: string; className: string }> = [
  { type: 'condition', label: '条件控制节点', description: '条件判断与分支路由', className: 'border-emerald-300 bg-emerald-50 text-emerald-950' },
  { type: 'parallel', label: '并行控制节点', description: '在决策后并列推进多个执行智能体', className: 'border-cyan-300 bg-cyan-50 text-cyan-950' },
  { type: 'approval', label: '审批节点', description: '审批挂起与恢复', className: 'border-amber-300 bg-amber-50 text-amber-950' },
  { type: 'wait', label: '等待节点', description: '等待事件或时间', className: 'border-slate-300 bg-slate-50 text-slate-900' },
  { type: 'exception', label: '异常控制节点', description: '异常兜底与风险处理', className: 'border-fuchsia-300 bg-fuchsia-50 text-fuchsia-950' },
]

const displayedNodes = computed(() => (activeTab.value === 'agents' ? agentNodes : controlNodes))

const addNode = (type: WorkflowNodeType, label: string) => {
  workflowStore.addNode(type, label)
  workflowStore.closeNodePicker()
}

const closePicker = () => {
  workflowStore.closeNodePicker()
}
</script>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
