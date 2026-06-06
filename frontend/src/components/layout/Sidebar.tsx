import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard, Building2, Users, UserCircle, Target, FolderKanban,
  FileText, Wallet, HardHat, ShoppingCart, Warehouse, Home, Headphones,
  Settings, ScrollText, CreditCard, Bot,
} from 'lucide-react'

const superAdminLinks = [
  { to: '/super-admin', icon: LayoutDashboard, label: 'dashboard' },
  { to: '/super-admin/companies', icon: Building2, label: 'companies' },
  { to: '/super-admin/users', icon: Users, label: 'users' },
  { to: '/super-admin/subscriptions', icon: CreditCard, label: 'subscriptions' },
  { to: '/super-admin/audit-logs', icon: ScrollText, label: 'audit_logs' },
  { to: '/super-admin/settings', icon: Settings, label: 'settings' },
]

const companyLinks = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'dashboard' },
  { to: '/customers', icon: UserCircle, label: 'customers' },
  { to: '/leads', icon: Target, label: 'leads' },
  { to: '/projects', icon: FolderKanban, label: 'projects' },
  { to: '/reservations', icon: FileText, label: 'reservations' },
  { to: '/contracts', icon: FileText, label: 'contracts' },
  { to: '/collections', icon: Wallet, label: 'collections' },
  { to: '/brokers', icon: Users, label: 'brokers' },
  { to: '/finance', icon: Wallet, label: 'finance' },
  { to: '/construction', icon: HardHat, label: 'construction' },
  { to: '/procurement', icon: ShoppingCart, label: 'procurement' },
  { to: '/warehouse', icon: Warehouse, label: 'warehouse' },
  { to: '/property', icon: Home, label: 'property' },
  { to: '/customer-service', icon: Headphones, label: 'customer_service' },
  { to: '/ai-assistant', icon: Bot, label: 'ai_assistant' },
]

export function Sidebar() {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const links = user?.is_super_admin ? superAdminLinks : companyLinks

  return (
    <aside className="flex h-full w-64 flex-col border-e border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-700 text-lg font-bold text-accent-500">
            F
          </div>
          <div>
            <h1 className="text-lg font-bold text-primary-800">{t('platform')}</h1>
            <p className="text-xs text-slate-500">{user?.is_super_admin ? t('super_admin') : t('company_admin')}</p>
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
