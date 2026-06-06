import { create } from 'zustand'
import api from '@/lib/api'

export interface CompanyProfile {
  id: number
  name_ar: string
  name_en: string
  code: string
  logo_url?: string
  theme: string
  currency: string
  city?: string
  country: string
}

interface CompanyState {
  company: CompanyProfile | null
  loading: boolean
  fetchCompany: () => Promise<void>
  setCompany: (company: CompanyProfile) => void
  clear: () => void
}

export const useCompanyStore = create<CompanyState>((set) => ({
  company: null,
  loading: false,
  fetchCompany: async () => {
    set({ loading: true })
    try {
      const { data } = await api.get<CompanyProfile>('/companies/me')
      set({ company: data })
    } catch {
      set({ company: null })
    } finally {
      set({ loading: false })
    }
  },
  setCompany: (company) => set({ company }),
  clear: () => set({ company: null }),
}))
