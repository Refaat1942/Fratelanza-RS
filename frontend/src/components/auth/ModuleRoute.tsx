import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { useModulesStore } from '@/stores/modulesStore'
import { COMPANY_MODULE_LINKS } from '@/config/modules'

interface ModuleRouteProps {
  moduleKey: string
  children: ReactNode
}

export function ModuleRoute({ moduleKey, children }: ModuleRouteProps) {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const { enabled, loaded, isEnabled } = useModulesStore()

  if (user?.is_super_admin) return <>{children}</>
  if (!loaded) return <p className="text-slate-500">{t('loading')}</p>
  if (isEnabled(moduleKey)) return <>{children}</>

  const fallback = COMPANY_MODULE_LINKS.find((l) => enabled.includes(l.moduleKey))?.route ?? '/dashboard'
  return <Navigate to={fallback} replace />
}
