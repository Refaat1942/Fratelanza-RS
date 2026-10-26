import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ShieldAlert } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { useModulesStore } from '@/stores/modulesStore'
import { usePermissionsStore } from '@/stores/permissionsStore'
import { COMPANY_MODULE_LINKS } from '@/config/modules'

interface ModuleRouteProps {
  moduleKey: string
  children: ReactNode
}

/** UX guard for direct URL access. The backend independently rejects every unauthorised API call. */
export function ModuleRoute({ moduleKey, children }: ModuleRouteProps) {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const { enabled, loaded, isEnabled } = useModulesStore()
  const perms = usePermissionsStore()

  if (user?.is_super_admin) return <>{children}</>
  if (!loaded || !perms.loaded) return <p className="text-slate-500">{t('loading')}</p>
  if (perms.error && perms.error.startsWith('demo_')) {
    return (
      <div className="mx-auto mt-16 max-w-md rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center text-amber-900">
        <ShieldAlert className="mx-auto mb-3 h-10 w-10" />
        <p className="font-semibold">{t(`re.errors.${perms.error}`)}</p>
      </div>
    )
  }
  if (isEnabled(moduleKey) && perms.can(moduleKey, 'view')) return <>{children}</>

  const fallback = COMPANY_MODULE_LINKS.find((l) => enabled.includes(l.moduleKey) && perms.can(l.moduleKey, 'view'))?.route
  if (fallback && fallback !== window.location.pathname) return <Navigate to={fallback} replace />
  return (
    <div className="mx-auto mt-16 max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center text-slate-700">
      <ShieldAlert className="mx-auto mb-3 h-10 w-10 text-slate-400" />
      <p className="font-semibold">{t('re.errors.forbidden')}</p>
    </div>
  )
}
