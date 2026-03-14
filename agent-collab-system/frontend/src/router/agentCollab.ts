import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/workflow-canvas' },
  {
    path: '/workflow-canvas',
    name: 'workflow-canvas',
    component: () => import('@/pages/WorkflowCanvasPage.vue'),
  },
  {
    path: '/chat-workbench',
    name: 'chat-workbench',
    component: () => import('@/pages/ChatWorkbenchPage.vue'),
  },
  {
    path: '/monitor-workbench',
    name: 'monitor-workbench',
    component: () => import('@/pages/MonitorWorkbenchPage.vue'),
  },
  {
    path: '/workflow-library',
    name: 'workflow-library',
    component: () => import('@/pages/WorkflowLibraryPage.vue'),
  },
  {
    path: '/records-workbench',
    name: 'records-workbench',
    component: () => import('@/pages/RecordsWorkbenchPage.vue'),
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
