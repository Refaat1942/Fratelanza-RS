import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { KeyRound, LogOut, Menu } from 'lucide-react'
import { ChangePasswordModal } from '@/components/forms/ChangePasswordModal'
import { ReminderBell } from './ReminderBell'
import { useAuthStore } from '@/stores/authStore'
import { useCompanyStore } from '@/stores/companyStore'
import { useModulesStore } from '@/stores/modulesStore'
import { usePermissionsStore } from '@/stores/permissionsStore'
import { useUiStore } from '@/stores/uiStore'
import { LanguageSwitcher } from './LanguageSwitcher'
import { GlobalSearch } from './GlobalSearch'

export function Header() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const clearCompany = useCompanyStore((s) => s.clear)
  const clearModules = useModulesStore((s) => s.clear)
  const clearPermissions = usePermissionsStore((s) => s.clear)
  const setSidebarOpen = useUiStore((s) => s.setSidebarOpen)
  const [passwordOpen, setPasswordOpen] = useState(false)

  const handleLogout = () => {
    clearCompany()
    clearModules()
    clearPermissions()
    logout()
    navigate('/login')
  }

  const displayName = i18n.language === 'ar' ? user?.full_name_ar : user?.full_name_en

  return (
    <header className="flex h-16 items-center justify-between gap-2 border-b border-primary-100/80 bg-white/80 px-3 shadow-sm backdrop-blur-md sm:px-6">
      <div className="flex min-w-0 items-center gap-2">
        <button className="rounded-lg p-2 text-slate-700 hover:bg-slate-100 lg:hidden" onClick={() => setSidebarOpen(true)} aria-label={t('re.open_menu')}>
          <Menu className="h-5 w-5" />
        </button>
        <div className="hidden sm:block"><GlobalSearch /></div>
      </div>
      <div className="flex items-center gap-2">
        <LanguageSwitcher />
        {!user?.is_super_admin && <ReminderBell />}
        <div className="ms-1 flex items-center gap-1 border-s border-slate-200 ps-2 sm:ms-2 sm:gap-3 sm:ps-4">
          <div className="hidden text-end md:block">
            <p className="text-sm font-medium text-slate-900">{displayName}</p>
            <p className="text-xs text-slate-500">{user?.username ?? user?.email}</p>
          </div>
          <button onClick={() => setPasswordOpen(true)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100" title={t('change_password')}>
            <KeyRound className="h-5 w-5" />
          </button>
          <button onClick={handleLogout} className="rounded-lg p-2 text-slate-600 hover:bg-red-50 hover:text-red-600" title={t('logout')}>
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
      <ChangePasswordModal open={passwordOpen} onClose={() => setPasswordOpen(false)} />
    </header>
  )
}
