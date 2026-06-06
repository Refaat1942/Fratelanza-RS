import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Building2, Users, UserCircle } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import api from '@/lib/api'
import type { DashboardData } from '@/types'

export function SuperAdminDashboard() {
  const { t } = useTranslation()
  const { data, isLoading } = useQuery({
    queryKey: ['super-admin-dashboard'],
    queryFn: async () => {
      const { data } = await api.get<DashboardData>('/dashboard/super-admin')
      return data
    },
  })

  if (isLoading) return <p className="text-slate-500">{t('loading')}</p>

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('dashboard')}</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <StatCard title={t('companies')} value={String(data?.stats.total_companies ?? 0)} icon={Building2} />
        <StatCard title={t('users')} value={String(data?.stats.total_users ?? 0)} icon={Users} color="bg-emerald-50 text-emerald-700" />
        <StatCard title={t('customers')} value={String(data?.stats.total_customers ?? 0)} icon={UserCircle} color="bg-amber-50 text-amber-700" />
      </div>
    </div>
  )
}
