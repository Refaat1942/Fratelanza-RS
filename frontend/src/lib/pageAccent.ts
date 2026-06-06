/** Stable accent color index per route for PageHeader gradients */
const ROUTE_ACCENTS: Record<string, number> = {
  '/dashboard': 0,
  '/super-admin': 0,
  '/customers': 1,
  '/leads': 2,
  '/follow-ups': 3,
  '/projects': 4,
  '/reservations': 5,
  '/contracts': 0,
  '/collections': 1,
  '/brokers': 2,
  '/finance': 3,
  '/hr': 4,
  '/construction': 5,
  '/procurement': 0,
  '/warehouse': 1,
  '/property': 2,
  '/customer-service': 3,
  '/users': 4,
  '/reports': 5,
  '/branding': 0,
  '/ai-assistant': 1,
  '/super-admin/companies': 2,
  '/super-admin/users': 3,
  '/super-admin/subscriptions': 4,
  '/super-admin/settings': 5,
  '/super-admin/audit-logs': 0,
  '/super-admin/reports': 1,
}

export function accentForPath(pathname: string): number {
  if (ROUTE_ACCENTS[pathname] !== undefined) return ROUTE_ACCENTS[pathname]
  const base = '/' + pathname.split('/').filter(Boolean).slice(0, 2).join('/')
  return ROUTE_ACCENTS[base] ?? pathname.length % 6
}
