<template>
  <div class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
    <div class="mb-3 text-sm text-slate-400">节点配置</div>
    <DynamicFormRenderer />
  </div>
</template>

<script setup lang="ts">
import DynamicFormRenderer from '@/components/shared/DynamicFormRenderer.vue'
</script>
