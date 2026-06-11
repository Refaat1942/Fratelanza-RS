import { Outlet, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Building2, LogOut } from 'lucide-react'
import { AnimatedPage } from '@/components/ui/AnimatedPage'
import { Button } from '@/components/ui/Button'
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher'
import { useAuthStore } from '@/stores/authStore'

export function PortalLayout() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const handleLogout = () => {
    logout()
    navigate('/portal/login')
  }

  const displayName =
    user && (document.documentElement.lang === 'ar' ? user.full_name_ar : user.full_name_en)

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-primary-50/30 to-slate-100">
      <header className="sticky top-0 z-20 border-b border-white/60 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-700 text-white shadow-md">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-primary-900">{t('portal_title')}</p>
              <p className="text-xs text-slate-500">{t('portal_subtitle')}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {displayName && (
              <span className="hidden text-sm text-slate-600 sm:inline">{t('welcome')}, {displayName}</span>
            )}
            <LanguageSwitcher />
            <Button variant="secondary" onClick={handleLogout}>
              <LogOut className="me-1.5 h-4 w-4" />
              {t('logout')}
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        <AnimatedPage>
          <Outlet />
        </AnimatedPage>
      </main>
    </div>
  )
}
