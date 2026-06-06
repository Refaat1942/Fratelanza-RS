export interface DashboardStats {
  total_companies?: number
  total_users?: number
  total_projects?: number
  total_customers?: number
  total_leads?: number
  total_units?: number
  available_units?: number
  total_sales?: number
  total_collections?: number
  overdue_amount?: number
  open_tickets?: number
}

export interface KPICard {
  label_ar: string
  label_en: string
  value: string
  change_percent?: number
  trend?: string
}

export interface DashboardData {
  stats: DashboardStats
  kpis: KPICard[]
  sales_chart: { label: string; value: number }[]
  leads_pipeline: Record<string, number>
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Company {
  id: number
  name_ar: string
  name_en: string
  code: string
  status: string
  country: string
}

export interface Customer {
  id: number
  full_name_ar: string
  full_name_en: string
  mobile: string
  email?: string
}

export interface Lead {
  id: number
  full_name: string
  mobile: string
  source: string
  stage: string
  score: number
}
