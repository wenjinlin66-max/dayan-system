import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

import { useAuthStore } from '@/store/auth'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/chat-workbench' },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/workflow-canvas',
    name: 'workflow-canvas',
    component: () => import('@/pages/WorkflowCanvasPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat-workbench',
    name: 'chat-workbench',
    component: () => import('@/pages/ChatWorkbenchPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/monitor-workbench',
    name: 'monitor-workbench',
    component: () => import('@/pages/MonitorWorkbenchPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/workflow-library',
    name: 'workflow-library',
    component: () => import('@/pages/WorkflowLibraryPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records-workbench',
    name: 'records-workbench',
    component: () => import('@/pages/RecordsWorkbenchPage.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false
  if (requiresAuth && !authStore.isAuthenticated) {
    return '/login'
  }
  if (to.path === '/login' && authStore.isAuthenticated) {
    return '/chat-workbench'
  }
  return true
})

export default router
