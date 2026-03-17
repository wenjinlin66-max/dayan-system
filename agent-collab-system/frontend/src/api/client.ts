import axios from 'axios'
import type { AxiosError } from 'axios'

import { useAuthStore } from '@/store/auth'
import { getChatIdentityProfile, loadStoredChatIdentityContext } from '@/utils/chatIdentity'

export const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.isAuthenticated && authStore.identity) {
    config.headers.set('Authorization', `Bearer ${authStore.accessToken}`)
    config.headers.delete('x-user-id')
    config.headers.delete('x-dept-id')
    config.headers.delete('x-roles')
    return config
  }
  const context = loadStoredChatIdentityContext()
  const profile = getChatIdentityProfile(context.profileId)
  const effectiveDeptId = profile.roles.includes('ceo')
    ? context.scopeDeptId || 'ceo'
    : profile.deptId

  config.headers.set('x-user-id', profile.userId)
  config.headers.set('x-dept-id', effectiveDeptId)
  if (profile.roles.length > 0) {
    config.headers.set('x-roles', profile.roles.join(','))
  } else {
    config.headers.delete('x-roles')
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const authStore = useAuthStore()
    if (error.response?.status === 401 && authStore.isAuthenticated) {
      authStore.clearSession()
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.replace('/login')
      }
    }
    return Promise.reject(error)
  },
)
