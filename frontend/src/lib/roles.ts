import type { User } from '@/stores/authStore'

export const COMPANY_ADMIN_ROLES = ['company_admin', 'ceo', 'managing_director'] as const

export const ASSIGNABLE_ROLES = [
  'company_admin',
  'ceo',
  'managing_director',
  'sales_director',
  'sales_manager',
  'sales_agent',
  'collection_officer',
  'accountant',
  'finance_manager',
  'customer_service',
  'hr_officer',
  'procurement_officer',
  'project_manager',
  'engineer',
] as const

export function isCompanyAdmin(user: User | null | undefined): boolean {
  if (!user) return false
  if (user.is_super_admin) return true
  return COMPANY_ADMIN_ROLES.includes(user.system_role as typeof COMPANY_ADMIN_ROLES[number])
}

export const ROLE_DEFAULT_MODULES: Record<string, string[]> = {
  company_admin: ['users', 'settings', 'all_modules'],
  ceo: ['users', 'settings', 'reports', 'finance', 'hr'],
  managing_director: ['users', 'settings', 'reports', 'finance'],
  sales_director: ['customers', 'leads', 'reservations', 'contracts', 'brokers', 'reports'],
  sales_manager: ['customers', 'leads', 'reservations', 'contracts', 'reports'],
  sales_agent: ['customers', 'leads', 'reservations', 'follow_ups'],
  collection_officer: ['collections', 'contracts', 'customers', 'reports'],
  accountant: ['finance', 'collections', 'reports'],
  finance_manager: ['finance', 'collections', 'reports'],
  customer_service: ['customers', 'customer_service', 'follow_ups', 'tickets'],
  hr_officer: ['hr', 'reports'],
  procurement_officer: ['procurement', 'warehouse', 'construction'],
  project_manager: ['projects', 'construction', 'warehouse'],
  engineer: ['construction', 'projects', 'warehouse'],
}
