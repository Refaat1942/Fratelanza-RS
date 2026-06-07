export const COMPANY_USER_ROLES = [
  'company_admin',
  'ceo',
  'managing_director',
  'sales_director',
  'sales_manager',
  'sales_agent',
  'customer_service',
  'collection_officer',
  'accountant',
  'finance_manager',
  'procurement_officer',
  'project_manager',
  'engineer',
  'hr_manager',
  'broker',
]

export function formatRole(role?: string) {
  return role ? role.replace(/_/g, ' ') : '-'
}
