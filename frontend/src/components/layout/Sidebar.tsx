import { useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { useCompanyStore } from '@/stores/companyStore'
import { useModulesStore } from '@/stores/modulesStore'
import { usePermissionsStore } from '@/stores/permissionsStore'
import { useUiStore } from '@/stores/uiStore'
import { COMPANY_MODULE_LINKS } from '@/config/modules'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard, Building2, Users, UserCircle, Target, FolderKanban,
  FileText, Wallet, HardHat, ShoppingCart, Warehouse, Home, Headphones,
  Settings, ScrollText, CreditCard, Bot, BarChart3, Phone, Palette,
  KeyRound, Receipt, Landmark, Search as SearchIcon, Presentation, X,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || ''

const LINK_ICONS: Record<string, LucideIcon> = { '/roles': KeyRound }

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
  property: Home,
  customer_service: Headphones,
  users: Users,
  customer_portal: Building2,
  reports: BarChart3,
  hr: Users,
  branding: Palette,
  ai_assistant: Bot,
  real_estate_requests: SearchIcon,
  rentals: Home,
  owners: Landmark,
  property_expenses: Receipt,
  admin_expenses: Receipt,
}

const superAdminLinks = [
  { to: '/super-admin', icon: LayoutDashboard, label: 'dashboard' },
  { to: '/super-admin/companies', icon: Building2, label: 'companies' },
  { to: '/super-admin/users', icon: Users, label: 'users' },
  { to: '/super-admin/subscriptions', icon: CreditCard, label: 'subscriptions' },
  { to: '/super-admin/demos', icon: Presentation, label: 're.nav.demos' },
  { to: '/super-admin/audit-logs', icon: ScrollText, label: 'audit_logs' },
  { to: '/super-admin/settings', icon: Settings, label: 'settings' },
  { to: '/super-admin/reports', icon: BarChart3, label: 'reports' },
]

export function Sidebar() {
  const { t, i18n } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const { company, fetchCompany } = useCompanyStore()
  const { fetchModules, isEnabled } = useModulesStore()
  const { fetch: fetchPermissions, can } = usePermissionsStore()
  const { sidebarOpen, setSidebarOpen } = useUiStore()
  const location = useLocation()

  const userId = user?.id
  const isSuperAdmin = user?.is_super_admin
  useEffect(() => {
    if (userId && !isSuperAdmin) {
      fetchCompany()
      fetchModules()
      fetchPermissions()
    }
  }, [userId, isSuperAdmin, fetchCompany, fetchModules, fetchPermissions])

  useEffect(() => { setSidebarOpen(false) }, [location.pathname, setSidebarOpen])

  const companyLinks = COMPANY_MODULE_LINKS
    .filter((l) => user?.is_super_admin || (isEnabled(l.moduleKey) && can(l.moduleKey, 'view')))
    .map((l) => ({
      to: l.route,
      icon: LINK_ICONS[l.route] ?? MODULE_ICONS[l.moduleKey] ?? LayoutDashboard,
      label: l.label,
    }))

  if (!user?.is_super_admin && isEnabled('users') && can('users', 'manage_permissions')) {
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
    <>
    {sidebarOpen && <div className="fixed inset-0 z-30 bg-slate-900/50 lg:hidden" onClick={() => setSidebarOpen(false)} aria-hidden />}
    <aside
      className={cn(
        'sidebar-shell fixed inset-y-0 start-0 z-40 transition-transform duration-200 lg:static lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : 'max-lg:ltr:-translate-x-full max-lg:rtl:translate-x-full',
      )}
    >
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
          <button className="ms-auto rounded-lg p-1.5 text-white/80 hover:bg-white/10 lg:hidden" onClick={() => setSidebarOpen(false)} aria-label={t('re.close_menu')}>
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to + label}
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
    </>
  )
}
