import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { isCompanyAdmin } from '@/lib/roles'
import { Card } from '@/components/ui/Card'
import { Shield } from 'lucide-react'

interface AdminRouteProps {
  children: ReactNode
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)

  if (!user) return <Navigate to="/login" replace />
  if (user.is_super_admin) return <>{children}</>
  if (isCompanyAdmin(user)) return <>{children}</>

  return (
    <div className="flex min-h-[50vh] items-center justify-center p-6">
      <Card className="max-w-md text-center">
        <Shield className="mx-auto mb-4 h-12 w-12 text-amber-500" />
        <h2 className="text-lg font-semibold text-slate-900">{t('settings_admin_only_title')}</h2>
        <p className="mt-2 text-sm text-slate-600">{t('settings_admin_only_help')}</p>
      </Card>
    </div>
  )
}
