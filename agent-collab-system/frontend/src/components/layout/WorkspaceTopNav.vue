<template>
  <div class="mb-5 rounded-[28px] border border-slate-200/80 bg-white/92 px-5 py-4 shadow-[0_18px_50px_rgba(148,163,184,0.12)] backdrop-blur">
    <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
      <div>
        <div class="text-[11px] uppercase tracking-[0.28em] text-sky-700/70">Dayan Workspaces</div>
        <div class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{{ title }}</div>
        <div v-if="description" class="mt-1 text-sm text-slate-500">{{ description }}</div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to">
          <button
            class="rounded-full border px-4 py-2 text-sm font-medium transition"
            :class="isActive(item.to)
              ? 'border-sky-300 bg-sky-50 text-sky-900 shadow-sm shadow-sky-100/80'
              : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'"
          >
            {{ item.label }}
          </button>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

defineProps<{
  title: string
  description?: string
}>()

const route = useRoute()

const navItems = computed(() => [
  { label: '工作流制作区', to: '/workflow-canvas' },
  { label: '工作流查看区', to: '/workflow-library' },
  { label: '对话区', to: '/chat-workbench' },
  { label: '监控区', to: '/monitor-workbench' },
  { label: '业务表格区', to: '/records-workbench' },
])

const isActive = (to: string) => route.path === to
</script>
