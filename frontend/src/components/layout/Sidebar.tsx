import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { useCompanyStore } from '@/stores/companyStore'
import { useModulesStore } from '@/stores/modulesStore'
import { COMPANY_MODULE_LINKS } from '@/config/modules'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard, Building2, Users, UserCircle, Target, FolderKanban,
  FileText, Wallet, HardHat, ShoppingCart, Warehouse, Home, Headphones, Files,
  Settings, ScrollText, CreditCard, Bot, BarChart3, Phone, Palette,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || ''

const MODULE_ICONS: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  customers: UserCircle,
  leads: Target,
  follow_ups: Phone,
  projects: FolderKanban,
  reservations: FileText,
  contracts: FileText,
  collections: Wallet,
  brokers: Users,
  finance: Wallet,
  construction: HardHat,
  procurement: ShoppingCart,
  warehouse: Warehouse,
  documents: Files,
  property: Home,
  customer_service: Headphones,
  users: Users,
  reports: BarChart3,
  hr: Users,
  branding: Palette,
  ai_assistant: Bot,
}

const superAdminLinks = [
  { to: '/super-admin', icon: LayoutDashboard, label: 'dashboard' },
  { to: '/super-admin/companies', icon: Building2, label: 'companies' },
  { to: '/super-admin/users', icon: Users, label: 'users' },
  { to: '/super-admin/subscriptions', icon: CreditCard, label: 'subscriptions' },
  { to: '/super-admin/audit-logs', icon: ScrollText, label: 'audit_logs' },
  { to: '/super-admin/settings', icon: Settings, label: 'settings' },
  { to: '/super-admin/reports', icon: BarChart3, label: 'reports' },
]

export function Sidebar() {
  const { t, i18n } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const { company, fetchCompany } = useCompanyStore()
  const { fetchModules, isEnabled } = useModulesStore()

  useEffect(() => {
    if (user && !user.is_super_admin) {
      fetchCompany()
      fetchModules()
    }
  }, [user, fetchCompany, fetchModules])

  const companyLinks = COMPANY_MODULE_LINKS
    .filter((l) => user?.is_super_admin || isEnabled(l.moduleKey))
    .map((l) => ({
      to: l.route,
      icon: MODULE_ICONS[l.moduleKey] ?? LayoutDashboard,
      label: l.label,
    }))

  if (!user?.is_super_admin && isEnabled('users')) {
    companyLinks.push({
      to: '/feature-settings',
      icon: Settings,
      label: 'feature_settings',
    })
  }

  const links = user?.is_super_admin ? superAdminLinks : companyLinks

  const displayName = company
    ? (i18n.language === 'ar' ? company.name_ar : company.name_en)
    : t('platform')
  const logoSrc = company?.logo_url
    ? (company.logo_url.startsWith('http') ? company.logo_url : `${API_URL}${company.logo_url}`)
    : null

  return (
    <aside className="sidebar-shell">
      <div className="border-b border-white/10 p-6">
        <div className="flex items-center gap-3">
          {logoSrc ? (
            <img src={logoSrc} alt="" className="h-10 w-10 rounded-xl border border-white/20 object-contain shadow-lg" />
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent-500 to-primary-400 text-lg font-bold text-white shadow-lg animate-glow">
              {(displayName || 'F').charAt(0)}
            </div>
          )}
          <div className="min-w-0">
            <h1 className="truncate text-lg font-bold text-white">{displayName}</h1>
            <p className="text-xs font-medium text-primary-100">{user?.is_super_admin ? t('super_admin') : t('company_admin')}</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/dashboard' || to === '/super-admin'}
            className={({ isActive }) => cn('sidebar-link', isActive && 'sidebar-link-active')}
          >
            <Icon className="h-5 w-5" />
            <span>{t(label)}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
