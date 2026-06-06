import { create } from 'zustand'
import api from '@/lib/api'

export interface ModuleCatalogItem {
  key: string
  name_en: string
  name_ar: string
  category_en: string
  category_ar: string
  route: string
  core: boolean
}

interface ModulesState {
  enabled: string[]
  catalog: ModuleCatalogItem[]
  loaded: boolean
  fetchModules: () => Promise<void>
  isEnabled: (key: string) => boolean
  clear: () => void
}

export const useModulesStore = create<ModulesState>((set, get) => ({
  enabled: [],
  catalog: [],
  loaded: false,
  fetchModules: async () => {
    try {
      const { data } = await api.get<{ enabled: string[]; catalog: ModuleCatalogItem[] }>('/modules/me')
      set({ enabled: data.enabled ?? [], catalog: data.catalog ?? [], loaded: true })
    } catch {
      set({ enabled: [], catalog: [], loaded: true })
    }
  },
  isEnabled: (key: string) => {
    const { enabled } = get()
    return enabled.length === 0 || enabled.includes(key)
  },
  clear: () => set({ enabled: [], catalog: [], loaded: false }),
}))
