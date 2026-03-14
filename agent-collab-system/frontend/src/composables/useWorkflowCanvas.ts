import { computed, ref } from 'vue'

import { useWorkflowStore } from '@/store/workflow'

export const useWorkflowCanvas = () => {
  const workflowStore = useWorkflowStore()
  const edgeSource = ref('')
  const edgeTarget = ref('')

  const connectNodes = () => {
    workflowStore.addEdge(edgeSource.value, edgeTarget.value)
  }

  const updateNodePosition = (nodeId: string, position: { x: number; y: number }) => {
    workflowStore.updateNodePosition(nodeId, position)
  }

  return {
    initialized: computed(() => workflowStore.nodes.length > 0),
    nodes: computed(() => workflowStore.nodes),
    edges: computed(() => workflowStore.edges),
    selectedNode: computed(() => workflowStore.selectedNode),
    edgeSource,
    edgeTarget,
    initializeDemoFlow: workflowStore.initializeDemoFlow,
    addNode: workflowStore.addNode,
    selectNode: workflowStore.selectNode,
    connectNodes,
    updateNodePosition,
  }
}
