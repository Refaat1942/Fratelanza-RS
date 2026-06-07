export const SYSTEM_ROLES = [
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
  'customer',
]

export function roleLabel(role: string) {
  return role.replace(/_/g, ' ')
}
