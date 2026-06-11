import { create } from 'zustand'
import api from '@/lib/api'

export interface PortalFeatureCatalogItem {
  key: string
  name_en: string
  name_ar: string
  description_en: string
  description_ar: string
  core: boolean
}

interface PortalFeaturesState {
  enabled: string[]
  catalog: PortalFeatureCatalogItem[]
  loaded: boolean
  fetchFeatures: () => Promise<void>
  isEnabled: (key: string) => boolean
  clear: () => void
}

export const usePortalFeaturesStore = create<PortalFeaturesState>((set, get) => ({
  enabled: [],
  catalog: [],
  loaded: false,
  fetchFeatures: async () => {
    try {
      const { data } = await api.get<{ enabled: string[]; catalog: PortalFeatureCatalogItem[] }>(
        '/customer-portal/me',
      )
      set({ enabled: data.enabled ?? [], catalog: data.catalog ?? [], loaded: true })
    } catch {
      set({ enabled: ['dashboard'], catalog: [], loaded: true })
    }
  },
  isEnabled: (key: string) => {
    const { enabled, loaded } = get()
    if (!loaded) return key === 'dashboard'
    return enabled.includes(key)
  },
  clear: () => set({ enabled: [], catalog: [], loaded: false }),
}))
