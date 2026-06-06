import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { DollarSign, Wallet, Home, Target, BarChart3 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { StatCard } from '@/components/ui/StatCard'
import { SalesChart } from '@/components/dashboard/SalesChart'
import { PipelineChart } from '@/components/dashboard/PipelineChart'
import { ActionPanel } from '@/components/dashboard/ActionPanel'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import type { DashboardData } from '@/types'

export function CompanyDashboard() {
  const { t, i18n } = useTranslation()
  const { formatEGP, formatInteger } = useFormatNumber()
  const navigate = useNavigate()
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
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t('dashboard')}</h1>
        <Button variant="secondary" onClick={() => navigate('/reports')}>
          <BarChart3 className="me-2 h-4 w-4" />
          {t('view_reports')}
        </Button>
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={formatKpi(0, t('total_sales'))}
          value={formatEGP(data?.stats.total_sales)}
          icon={DollarSign}
        />
        <StatCard
          title={formatKpi(1, t('total_collections'))}
          value={formatEGP(data?.stats.total_collections)}
          icon={Wallet}
          color="bg-emerald-50 text-emerald-700"
        />
        <StatCard
          title={formatKpi(2, t('available_units'))}
          value={formatInteger(data?.stats.available_units)}
          icon={Home}
          color="bg-amber-50 text-amber-700"
        />
        <StatCard
          title={formatKpi(3, t('active_leads'))}
          value={formatInteger(data?.stats.total_leads)}
          icon={Target}
          color="bg-violet-50 text-violet-700"
        />
      </div>
      <ActionPanel />
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <SalesChart data={data?.sales_chart ?? []} />
        <PipelineChart pipeline={data?.leads_pipeline ?? {}} />
      </div>
    </div>
  )
}
