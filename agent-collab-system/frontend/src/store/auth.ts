import { defineStore } from 'pinia'

import type { AuthIdentity, AuthLoginResponse } from '@/types/auth'

type StoredAuthSession = {
  accessToken: string
  identity: AuthIdentity
}

const STORAGE_KEY = 'dayan-auth-session'

const loadStoredAuthSession = (): StoredAuthSession | null => {
  if (typeof window === 'undefined') {
    return null
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as StoredAuthSession) : null
  } catch {
    return null
  }
}

const persistAuthSession = (value: StoredAuthSession | null) => {
  if (typeof window === 'undefined') {
    return
  }
  if (!value) {
    window.localStorage.removeItem(STORAGE_KEY)
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: loadStoredAuthSession()?.accessToken ?? '',
    identity: loadStoredAuthSession()?.identity ?? null as AuthIdentity | null,
    loginSubmitting: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.identity),
    isCEO: (state) => Boolean(state.identity?.roles.includes('ceo')),
  },
  actions: {
    setSession(payload: AuthLoginResponse) {
      this.accessToken = payload.access_token
      this.identity = payload.identity
      persistAuthSession({ accessToken: payload.access_token, identity: payload.identity })
    },
    clearSession() {
      this.accessToken = ''
      this.identity = null
      persistAuthSession(null)
    },
    setLoginSubmitting(value: boolean) {
      this.loginSubmitting = value
    },
  },
})
