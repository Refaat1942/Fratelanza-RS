import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Bell, LogOut } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { LanguageSwitcher } from './LanguageSwitcher'
import { GlobalSearch } from './GlobalSearch'

export function Header() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const displayName = i18n.language === 'ar' ? user?.full_name_ar : user?.full_name_en

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <GlobalSearch />
      <div className="flex items-center gap-2">
        <LanguageSwitcher />
        <button className="rounded-lg p-2 text-slate-600 hover:bg-slate-100">
          <Bell className="h-5 w-5" />
        </button>
        <div className="ms-2 flex items-center gap-3 border-s border-slate-200 ps-4">
          <div className="text-end">
            <p className="text-sm font-medium text-slate-900">{displayName}</p>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>
          <button onClick={handleLogout} className="rounded-lg p-2 text-slate-600 hover:bg-red-50 hover:text-red-600" title={t('logout')}>
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  )
}
