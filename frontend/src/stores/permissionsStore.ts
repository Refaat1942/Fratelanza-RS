import { create } from 'zustand'
import api from '@/lib/api'

/** Effective permissions of the signed-in user (display only — the API authorises every call). */
export interface EffectivePermissions {
  user_id: number
  company_id: number | null
  is_super_admin: boolean
  is_demo: boolean
  enabled_modules: string[]
  permissions: Record<string, string[]>
  data_scope: string
  field_access: string[]
  dashboard_cards: string[] | null
  demo: { prospect_name: string; expires_at: string | null; profile: string } | null
}

interface PermissionsState {
  data: EffectivePermissions | null
  loaded: boolean
  error: string | null
  fetch: () => Promise<void>
  can: (module: string, action?: string) => boolean
  sees: (fieldGroup: string) => boolean
  clear: () => void
}

export const usePermissionsStore = create<PermissionsState>((set, get) => ({
  data: null,
  loaded: false,
  error: null,
  fetch: async () => {
    try {
      const { data } = await api.get<EffectivePermissions>('/auth/me/permissions')
      set({ data, loaded: true, error: null })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      set({ data: null, loaded: true, error: typeof detail === 'string' ? detail : 'error' })
    }
  },
  can: (module, action = 'view') => {
    const d = get().data
    if (!d) return false
    if (d.is_super_admin) return true
    return (d.permissions[module] ?? []).includes(action)
  },
  sees: (group) => {
    const d = get().data
    return !!d && (d.is_super_admin || d.field_access.includes(group))
  },
  clear: () => set({ data: null, loaded: false, error: null }),
}))
