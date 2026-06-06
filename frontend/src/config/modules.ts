export interface PlatformModule {
  key: string
  label: string
  route: string
  category: string
}

/** Sidebar module keys — must match backend platform_modules.py */
export const COMPANY_MODULE_LINKS: { moduleKey: string; route: string; label: string }[] = [
  { moduleKey: 'dashboard', route: '/dashboard', label: 'dashboard' },
  { moduleKey: 'customers', route: '/customers', label: 'customers' },
  { moduleKey: 'leads', route: '/leads', label: 'leads' },
  { moduleKey: 'follow_ups', route: '/follow-ups', label: 'follow_ups' },
  { moduleKey: 'projects', route: '/projects', label: 'projects' },
  { moduleKey: 'reservations', route: '/reservations', label: 'reservations' },
  { moduleKey: 'contracts', route: '/contracts', label: 'contracts' },
  { moduleKey: 'collections', route: '/collections', label: 'collections' },
  { moduleKey: 'brokers', route: '/brokers', label: 'brokers' },
  { moduleKey: 'finance', route: '/finance', label: 'finance' },
  { moduleKey: 'construction', route: '/construction', label: 'construction' },
  { moduleKey: 'procurement', route: '/procurement', label: 'procurement' },
  { moduleKey: 'warehouse', route: '/warehouse', label: 'warehouse' },
  { moduleKey: 'property', route: '/property', label: 'property' },
  { moduleKey: 'customer_service', route: '/customer-service', label: 'customer_service' },
  { moduleKey: 'users', route: '/users', label: 'users' },
  { moduleKey: 'reports', route: '/reports', label: 'reports' },
  { moduleKey: 'hr', route: '/hr', label: 'hr' },
  { moduleKey: 'branding', route: '/branding', label: 'branding' },
  { moduleKey: 'ai_assistant', route: '/ai-assistant', label: 'ai_assistant' },
]

export const ROUTE_MODULE_MAP: Record<string, string> = Object.fromEntries(
  COMPANY_MODULE_LINKS.map((l) => [l.route, l.moduleKey]),
)
