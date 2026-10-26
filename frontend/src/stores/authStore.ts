import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface User {
  id: number
  username?: string
  email?: string | null
  full_name_ar: string
  full_name_en: string
  system_role: string
  is_super_admin: boolean
  company_id?: number
  preferred_language: string
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setAuth: (accessToken: string, refreshToken: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setAuth: (accessToken, refreshToken, user) =>
        set({ accessToken, refreshToken, user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: 'fratelanza-auth' },
  ),
)
