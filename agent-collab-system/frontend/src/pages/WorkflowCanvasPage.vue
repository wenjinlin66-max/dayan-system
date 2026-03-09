<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 p-6">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">智能体协同画布</h1>
        <p class="text-sm text-slate-400">工作流草稿、编译、发布与节点配置入口</p>
      </div>
      <div class="flex gap-3">
        <el-button type="primary">保存草稿</el-button>
        <el-button>编译</el-button>
        <el-button type="success">发布</el-button>
      </div>
    </div>
    <div class="grid grid-cols-[260px_1fr_320px] gap-4">
      <NodePalette />
      <WorkflowCanvas />
      <NodeConfigPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import WorkflowCanvas from '@/components/canvas/WorkflowCanvas.vue'
import NodePalette from '@/components/canvas/NodePalette.vue'
import NodeConfigPanel from '@/components/canvas/NodeConfigPanel.vue'
</script>
