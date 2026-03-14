<template>
  <div class="rounded-[24px] border border-slate-200/80 bg-white/96 p-4 shadow-[0_18px_40px_rgba(148,163,184,0.10)]">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <div class="text-[11px] uppercase tracking-[0.22em] text-slate-500">多模态输入</div>
        <div class="mt-1 text-sm font-semibold text-slate-900">附件入口</div>
      </div>
      <div class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] text-slate-500">单入口</div>
    </div>
    <el-dropdown trigger="click">
      <el-button class="w-full justify-between" plain>
        选择附件或语音方式
        <span class="text-xs text-slate-400">PDF / 图片 / 语音</span>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item>上传 PDF</el-dropdown-item>
          <el-dropdown-item>上传图片</el-dropdown-item>
          <el-dropdown-item>语音输入</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    <div class="mt-3 text-xs leading-5 text-slate-500">
      默认隐藏具体入口，只有在你需要补充附件或语音时再展开选择。
    </div>
  </div>
</template>
