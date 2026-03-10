<template>
  <div class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
    <div class="mb-3 flex items-center justify-between">
      <div class="text-sm text-slate-400">部门工作流目录</div>
      <el-select placeholder="职能分类" class="!w-40">
        <el-option label="全部" value="all" />
      </el-select>
    </div>
    <div class="space-y-2">
      <div class="rounded-lg border border-slate-700 px-3 py-2 text-sm">补货申请流</div>
      <div class="rounded-lg border border-slate-700 px-3 py-2 text-sm">异常审批流</div>
    </div>
  </div>
</template>
