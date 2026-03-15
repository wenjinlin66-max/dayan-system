<template>
  <path
    :d="edgePath"
    fill="none"
    stroke="transparent"
    stroke-width="24"
    class="cursor-pointer"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
  />
  <BaseEdge :path="edgePath" :marker-end="markerEnd" :style="edgeStyle" />
  <EdgeLabelRenderer>
    <button
      v-show="hovered || selected"
      class="nodrag nopan absolute flex h-7 w-7 items-center justify-center rounded-full border border-rose-200 bg-white text-xs text-rose-500 shadow-[0_10px_20px_rgba(244,63,94,0.18)] transition hover:border-rose-300 hover:bg-rose-50 hover:text-rose-600"
      :style="labelStyle"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
      @click.stop="handleDelete"
    >
      ×
    </button>
  </EdgeLabelRenderer>
</template>

<script setup lang="ts">
import { computed, ref, type CSSProperties } from 'vue'
import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@vue-flow/core'

import { useWorkflowStore } from '@/store/workflow'

const props = defineProps<EdgeProps>()
const workflowStore = useWorkflowStore()
const hovered = ref(false)

const edgeStyle = computed(() => ({
  stroke: props.selected ? '#0ea5e9' : '#38bdf8',
  strokeWidth: props.selected ? 2.6 : 2,
}))

const edgeGeometry = computed(() => {
  const [path, labelX, labelY] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    targetX: props.targetX,
    targetY: props.targetY,
    sourcePosition: props.sourcePosition,
    targetPosition: props.targetPosition,
  })
  return { path, labelX, labelY }
})

const edgePath = computed(() => edgeGeometry.value.path)

const labelStyle = computed<CSSProperties>(() => ({
  pointerEvents: 'all',
  transform: `translate(-50%, -50%) translate(${edgeGeometry.value.labelX}px, ${edgeGeometry.value.labelY}px)`,
}))

const handleDelete = () => {
  workflowStore.deleteEdgeById(String(props.id))
}
</script>
