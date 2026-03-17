<template>
  <div
    class="group relative min-w-[220px] rounded-[24px] border px-4 py-3 shadow-[0_16px_35px_rgba(148,163,184,0.14)] transition"
    :class="containerClass"
  >
    <button
      class="absolute -left-2 -top-2 z-20 flex h-7 w-7 items-center justify-center rounded-full border border-rose-200 bg-white text-xs text-rose-500 opacity-0 shadow-[0_10px_20px_rgba(244,63,94,0.16)] transition group-hover:opacity-100 hover:border-rose-300 hover:bg-rose-50 hover:text-rose-600"
      @click.stop="handleDelete"
    >
      ×
    </button>
    <Handle type="target" :position="Position.Left" class="!h-3 !w-3 !border-0 !bg-slate-300" />
    <div class="mb-3 flex items-start justify-between gap-3">
      <span class="rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]" :class="badgeClass">
        {{ data.typeLabel || data.type }}
      </span>
      <span class="max-w-[120px] truncate text-[11px] text-slate-400">{{ id }}</span>
    </div>
    <div class="text-[22px] font-semibold tracking-tight text-slate-900">{{ data.label }}</div>
    <div class="mt-2 text-sm leading-6 text-slate-500 line-clamp-2">{{ data.description || '点击节点后打开配置面板' }}</div>
    <Handle type="source" :position="Position.Right" class="!h-3 !w-3 !border-0 !bg-sky-400" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position, type NodeProps } from '@vue-flow/core'

import { useWorkflowStore } from '@/store/workflow'

type WorkflowGraphNodeData = {
  label: string
  type: string
  typeLabel?: string
  description?: string
  isExecuting?: boolean
}

const props = defineProps<NodeProps<WorkflowGraphNodeData>>()
const workflowStore = useWorkflowStore()

const paletteMap: Record<string, { card: string; badge: string }> = {
  dialog_agent: {
    card: 'border-sky-300 bg-white',
    badge: 'bg-sky-100 text-sky-700',
  },
  sensor_agent: {
    card: 'border-cyan-300 bg-white',
    badge: 'bg-cyan-100 text-cyan-700',
  },
  decision_agent: {
    card: 'border-violet-300 bg-white',
    badge: 'bg-violet-100 text-violet-700',
  },
  execution_agent: {
    card: 'border-amber-300 bg-white',
    badge: 'bg-amber-100 text-amber-700',
  },
  condition: {
    card: 'border-emerald-300 bg-white',
    badge: 'bg-emerald-100 text-emerald-700',
  },
  parallel: {
    card: 'border-cyan-300 bg-white',
    badge: 'bg-cyan-100 text-cyan-700',
  },
  approval: {
    card: 'border-rose-300 bg-white',
    badge: 'bg-rose-100 text-rose-700',
  },
  wait: {
    card: 'border-slate-300 bg-white',
    badge: 'bg-slate-100 text-slate-700',
  },
  exception: {
    card: 'border-fuchsia-300 bg-white',
    badge: 'bg-fuchsia-100 text-fuchsia-700',
  },
}

const colorClass = computed(() => paletteMap[props.data.type]?.card ?? 'border-slate-300 bg-white')
const badgeClass = computed(() => paletteMap[props.data.type]?.badge ?? 'bg-slate-100 text-slate-700')
const containerClass = computed(() => {
  if (props.data.isExecuting) {
    return 'node-executing border-fuchsia-300 bg-white ring-2 ring-fuchsia-100'
  }
  if (props.selected) {
    return 'border-sky-400 bg-white shadow-sky-200/80 ring-2 ring-sky-100'
  }
  return colorClass.value
})

const handleDelete = () => {
  workflowStore.deleteNodeById(String(props.id))
}
</script>

<style scoped>
.node-executing {
  position: relative;
  overflow: hidden;
  box-shadow:
    0 0 0 1px rgba(236, 72, 153, 0.14),
    0 0 26px rgba(217, 70, 239, 0.28),
    0 0 46px rgba(59, 130, 246, 0.16),
    0 18px 44px rgba(168, 85, 247, 0.18);
  animation: nodeGlowPulse 1.8s ease-in-out infinite;
}

.node-executing::before {
  content: '';
  position: absolute;
  inset: -30%;
  background: conic-gradient(from 180deg, rgba(56, 189, 248, 0.12), rgba(168, 85, 247, 0.22), rgba(244, 114, 182, 0.18), rgba(56, 189, 248, 0.12));
  filter: blur(22px);
  animation: nodeAuroraSpin 3.2s linear infinite;
  pointer-events: none;
}

.node-executing > * {
  position: relative;
  z-index: 1;
}

@keyframes nodeGlowPulse {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-1px) scale(1.012);
  }
}

@keyframes nodeAuroraSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
