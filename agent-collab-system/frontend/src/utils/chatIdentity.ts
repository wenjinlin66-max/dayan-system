import type { ErpDepartmentValue } from './erpDepartments'

export type ChatScopeMode = 'department' | 'all_departments'

export type ChatIdentityProfile = {
  id: string
  label: string
  userId: string
  deptId: ErpDepartmentValue
  roles: string[]
}

export type StoredChatIdentityContext = {
  profileId: string
  scopeMode: ChatScopeMode
  scopeDeptId: string
}

export const CHAT_IDENTITY_PROFILES: ChatIdentityProfile[] = [
  { id: 'production_manager', label: '生产部账号 / 李工', userId: 'prod_li', deptId: 'production', roles: [] },
  { id: 'warehouse_manager', label: '仓储部账号 / 王仓', userId: 'warehouse_wang', deptId: 'warehouse', roles: [] },
  { id: 'supply_chain_manager', label: '供应链账号 / 周链', userId: 'supply_zhou', deptId: 'supply_chain', roles: [] },
  { id: 'ceo_console', label: 'CEO 账号 / 全局查看', userId: 'ceo_demo', deptId: 'ceo', roles: ['ceo'] },
]

const STORAGE_KEY = 'dayan-chat-identity'

const DEFAULT_CONTEXT: StoredChatIdentityContext = {
  profileId: 'production_manager',
  scopeMode: 'department',
  scopeDeptId: 'production',
}

export const loadStoredChatIdentityContext = (): StoredChatIdentityContext => {
  if (typeof window === 'undefined') {
    return DEFAULT_CONTEXT
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return DEFAULT_CONTEXT
    }
    const parsed = JSON.parse(raw) as Partial<StoredChatIdentityContext>
    return {
      profileId: typeof parsed.profileId === 'string' ? parsed.profileId : DEFAULT_CONTEXT.profileId,
      scopeMode: parsed.scopeMode === 'all_departments' ? 'all_departments' : 'department',
      scopeDeptId: typeof parsed.scopeDeptId === 'string' ? parsed.scopeDeptId : DEFAULT_CONTEXT.scopeDeptId,
    }
  } catch {
    return DEFAULT_CONTEXT
  }
}

export const saveStoredChatIdentityContext = (value: StoredChatIdentityContext) => {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
}

export const getChatIdentityProfile = (profileId: string) => {
  return CHAT_IDENTITY_PROFILES.find((item) => item.id === profileId) ?? CHAT_IDENTITY_PROFILES[0]
}

export const resolveProfileIdFromIdentity = (identity: { dept_id: string; roles: string[]; user_id: string }) => {
  if (identity.roles.includes('ceo')) {
    return 'ceo_console'
  }
  if (identity.user_id === 'warehouse_wang') {
    return 'warehouse_manager'
  }
  if (identity.user_id === 'supply_zhou') {
    return 'supply_chain_manager'
  }
  return 'production_manager'
}
