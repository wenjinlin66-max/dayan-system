<template>
  <div class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
    <div class="mb-4 text-sm text-slate-400">节点面板</div>
    <div class="space-y-2">
      <div v-for="node in nodes" :key="node" class="rounded-lg border border-slate-700 px-3 py-2 text-sm">
        {{ node }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const nodes = [
  'Sensor',
  'Decision',
  'Execution',
  'Dialog',
  'Monitor',
  'Condition',
  'Parallel',
  'Loop',
  'Subflow',
  'Wait',
  'Approval',
  'Exception',
]
</script>
