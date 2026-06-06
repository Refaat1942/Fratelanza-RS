import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { DollarSign, Wallet, Home, Target } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { SalesChart } from '@/components/dashboard/SalesChart'
import { PipelineChart } from '@/components/dashboard/PipelineChart'
import api from '@/lib/api'
import type { DashboardData } from '@/types'

export function CompanyDashboard() {
  const { t, i18n } = useTranslation()
  const { data, isLoading } = useQuery({
    queryKey: ['company-dashboard'],
    queryFn: async () => {
      const { data } = await api.get<DashboardData>('/dashboard/company')
      return data
    },
  })

  if (isLoading) return <p className="text-slate-500">{t('loading')}</p>

  const formatKpi = (index: number, fallback: string) => {
    const kpi = data?.kpis[index]
    if (!kpi) return fallback
    return i18n.language === 'ar' ? kpi.label_ar : kpi.label_en
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('dashboard')}</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={formatKpi(0, t('total_sales'))}
          value={data?.kpis[0]?.value ?? '0'}
          icon={DollarSign}
        />
        <StatCard
          title={formatKpi(1, t('total_collections'))}
          value={data?.kpis[1]?.value ?? '0'}
          icon={Wallet}
          color="bg-emerald-50 text-emerald-700"
        />
        <StatCard
          title={formatKpi(2, t('available_units'))}
          value={data?.kpis[2]?.value ?? '0'}
          icon={Home}
          color="bg-amber-50 text-amber-700"
        />
        <StatCard
          title={formatKpi(3, t('active_leads'))}
          value={data?.kpis[3]?.value ?? '0'}
          icon={Target}
          color="bg-violet-50 text-violet-700"
        />
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <SalesChart data={data?.sales_chart ?? []} />
        <PipelineChart pipeline={data?.leads_pipeline ?? {}} />
      </div>
    </div>
  )
}
