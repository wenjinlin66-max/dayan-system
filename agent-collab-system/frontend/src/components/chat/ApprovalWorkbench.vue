<template>
  <div class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
    <div class="mb-3 text-sm text-slate-400">审批工作区</div>
    <div class="space-y-3">
      <ApprovalCard />
      <el-input type="textarea" :rows="3" placeholder="输入审批意见" />
      <div class="flex gap-3">
        <el-button type="success">同意</el-button>
        <el-button type="danger">驳回</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ApprovalCard from './ApprovalCard.vue'
</script>
