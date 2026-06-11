import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  CalendarClock,
  Receipt,
  HardHat,
  FileText,
  Play,
} from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingState } from '@/components/ui/LoadingState'
import { StatCard } from '@/components/ui/StatCard'
import { Card, CardHeader } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { DataTable } from '@/components/ui/DataTable'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'overview' | 'installments' | 'payments' | 'progress'

interface DashboardData {
  customer: {
    id: number
    name_ar: string
    name_en: string
    mobile: string
    email: string | null
  }
  summary: {
    contracts_count: number
    total_remaining: number
    total_paid: number
    upcoming_installments: number
    receipts_count: number
  }
  contracts: Array<{
    id: number
    contract_number: string
    unit_code: string
    total_price: number
    remaining_balance: number
    status: string
    is_signed: boolean
  }>
  construction_phases: Array<{
    project_name_en: string
    project_name_ar: string
    phase_name_en: string
    phase_name_ar: string
    progress_percent: number
  }>
}

interface InstallmentRow {
  id: number
  contract_number: string
  unit_code: string
  installment_number: number
  due_date: string
  due_amount: number
  paid_amount: number
  remaining_balance: number
  status: string
}

interface PaymentRow {
  id: number
  receipt_number: string
  contract_number: string
  installment_number: number
  amount: number
  payment_date: string
  payment_method: string
  notes: string | null
}

interface ProgressUpdate {
  id: number
  project_name_en: string
  project_name_ar: string
  title_en: string
  title_ar: string
  description_en: string | null
  description_ar: string | null
  media_type: string
  media_url: string
  thumbnail_url: string | null
  progress_percent: number | null
  published_at: string
}

export function CustomerPortalPage() {
  const { t, i18n } = useTranslation()
  const { formatEGP, localizeDigits } = useFormatNumber()
  const [tab, setTab] = useState<Tab>('overview')
  const isAr = i18n.language === 'ar'

  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ['portal-dashboard'],
    queryFn: async () => (await api.get<DashboardData>('/customer-portal/dashboard')).data,
  })

  const { data: installments = [], isLoading: instLoading } = useQuery({
    queryKey: ['portal-installments'],
    queryFn: async () => (await api.get<InstallmentRow[]>('/customer-portal/installments')).data,
    enabled: tab === 'installments' || tab === 'overview',
  })

  const { data: payments = [], isLoading: payLoading } = useQuery({
    queryKey: ['portal-payments'],
    queryFn: async () => (await api.get<PaymentRow[]>('/customer-portal/payments')).data,
    enabled: tab === 'payments',
  })

  const { data: updates = [], isLoading: progLoading } = useQuery({
    queryKey: ['portal-progress'],
    queryFn: async () => (await api.get<ProgressUpdate[]>('/customer-portal/construction-updates')).data,
    enabled: tab === 'progress',
  })

  const tabs: { key: Tab; label: string; icon: typeof LayoutDashboard }[] = [
    { key: 'overview', label: t('overview'), icon: LayoutDashboard },
    { key: 'installments', label: t('portal_installments'), icon: CalendarClock },
    { key: 'payments', label: t('portal_receipts'), icon: Receipt },
    { key: 'progress', label: t('portal_construction'), icon: HardHat },
  ]

  if (dashLoading && tab === 'overview') return <LoadingState />

  const upcoming = installments.filter((i) =>
    ['upcoming', 'due', 'overdue', 'partial'].includes(i.status),
  )

  return (
    <div>
      <PageHeader
        title={t('portal_my_account')}
        subtitle={
          dashboard
            ? isAr
              ? dashboard.customer.name_ar
              : dashboard.customer.name_en
            : t('portal_subtitle')
        }
        icon={LayoutDashboard}
        accentIndex={2}
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={cn(
              'inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition',
              tab === key
                ? 'bg-primary-700 text-white shadow-md'
                : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50',
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'overview' && dashboard && (
        <>
          <div className="mb-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title={t('portal_total_paid')}
              value={formatEGP(dashboard.summary.total_paid)}
              icon={Receipt}
              color="bg-emerald-50 text-emerald-700"
            />
            <StatCard
              title={t('portal_remaining')}
              value={formatEGP(dashboard.summary.total_remaining)}
              icon={CalendarClock}
              color="bg-amber-50 text-amber-700"
            />
            <StatCard
              title={t('portal_upcoming_count')}
              value={localizeDigits(String(dashboard.summary.upcoming_installments))}
              icon={FileText}
            />
            <StatCard
              title={t('contracts')}
              value={localizeDigits(String(dashboard.summary.contracts_count))}
              icon={LayoutDashboard}
              color="bg-violet-50 text-violet-700"
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader title={t('contracts')} />
              {dashboard.contracts.length === 0 ? (
                <EmptyState title={t('no_data')} description={t('no_data_help')} />
              ) : (
                <ul className="space-y-3">
                  {dashboard.contracts.map((c) => (
                    <li
                      key={c.id}
                      className="rounded-xl border border-slate-100 bg-slate-50/80 px-4 py-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium text-slate-900">{c.contract_number}</p>
                          <p className="text-sm text-slate-500">
                            {t('units')}: {c.unit_code}
                          </p>
                        </div>
                        <span className="text-sm font-semibold text-primary-700">
                          {formatEGP(c.remaining_balance)} {t('portal_remaining_short')}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card>
              <CardHeader title={t('portal_construction_phases')} />
              {dashboard.construction_phases.length === 0 ? (
                <EmptyState title={t('portal_no_phases')} description={t('portal_no_phases_help')} />
              ) : (
                <ul className="space-y-4">
                  {dashboard.construction_phases.map((phase, idx) => {
                    const projectName = isAr ? phase.project_name_ar : phase.project_name_en
                    const phaseName = isAr ? phase.phase_name_ar : phase.phase_name_en
                    return (
                      <li key={idx}>
                        <div className="mb-1 flex justify-between text-sm">
                          <span className="font-medium text-slate-800">
                            {projectName} — {phaseName}
                          </span>
                          <span className="text-slate-500">
                            {localizeDigits(String(phase.progress_percent))}%
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                          <div
                            className="h-full rounded-full bg-primary-600 transition-all"
                            style={{ width: `${Math.min(100, phase.progress_percent)}%` }}
                          />
                        </div>
                      </li>
                    )
                  })}
                </ul>
              )}
            </Card>
          </div>

          {upcoming.length > 0 && (
            <div className="mt-6">
              <DataTable
                title={t('portal_next_installments')}
                subtitle={t('portal_next_installments_help')}
                data={upcoming.slice(0, 5) as unknown as Record<string, unknown>[]}
                loading={instLoading}
                searchable={false}
                columns={[
                  { key: 'contract_number', label: t('contracts') },
                  { key: 'installment_number', label: '#' },
                  { key: 'due_date', label: t('due_date') },
                  {
                    key: 'remaining_balance',
                    label: t('portal_remaining'),
                    render: (row) => formatEGP(row.remaining_balance as number),
                  },
                  { key: 'status', label: t('status') },
                ]}
              />
            </div>
          )}
        </>
      )}

      {tab === 'installments' && (
        <DataTable
          title={t('portal_installments')}
          subtitle={t('portal_installments_help')}
          data={installments as unknown as Record<string, unknown>[]}
          loading={instLoading}
          exportFilename="my-installments"
          columns={[
            { key: 'contract_number', label: t('contracts'), sortable: true },
            { key: 'unit_code', label: t('units'), sortable: true },
            { key: 'installment_number', label: '#', sortable: true },
            { key: 'due_date', label: t('due_date'), sortable: true },
            {
              key: 'due_amount',
              label: t('amount'),
              render: (row) => formatEGP(row.due_amount as number),
              sortable: true,
            },
            {
              key: 'paid_amount',
              label: t('portal_paid'),
              render: (row) => formatEGP(row.paid_amount as number),
            },
            {
              key: 'remaining_balance',
              label: t('portal_remaining'),
              render: (row) => formatEGP(row.remaining_balance as number),
            },
            { key: 'status', label: t('status'), sortable: true },
          ]}
        />
      )}

      {tab === 'payments' && (
        <DataTable
          title={t('portal_receipts')}
          subtitle={t('portal_receipts_help')}
          data={payments as unknown as Record<string, unknown>[]}
          loading={payLoading}
          exportFilename="payment-receipts"
          columns={[
            { key: 'receipt_number', label: t('portal_receipt_no'), sortable: true },
            { key: 'contract_number', label: t('contracts') },
            { key: 'installment_number', label: '#' },
            {
              key: 'amount',
              label: t('amount'),
              render: (row) => formatEGP(row.amount as number),
              sortable: true,
            },
            { key: 'payment_date', label: t('payment_date'), sortable: true },
            { key: 'payment_method', label: t('payment_method') },
          ]}
        />
      )}

      {tab === 'progress' && (
        <div>
          <PageHeader
            title={t('portal_construction')}
            subtitle={t('portal_construction_help')}
            icon={HardHat}
            accentIndex={3}
            className="mb-4"
          />
          {progLoading ? (
            <LoadingState />
          ) : updates.length === 0 ? (
            <EmptyState title={t('portal_no_updates')} description={t('portal_no_updates_help')} />
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              {updates.map((u) => {
                const title = isAr ? u.title_ar : u.title_en
                const desc = isAr ? u.description_ar : u.description_en
                const project = isAr ? u.project_name_ar : u.project_name_en
                return (
                  <Card key={u.id} className="overflow-hidden p-0">
                    <div className="relative aspect-video bg-slate-900">
                      {u.media_type === 'video' ? (
                        <>
                          <video
                            src={u.media_url}
                            controls
                            className="h-full w-full object-cover"
                            poster={u.thumbnail_url ?? undefined}
                          />
                          <span className="absolute start-3 top-3 inline-flex items-center gap-1 rounded-full bg-black/50 px-2 py-1 text-xs text-white">
                            <Play className="h-3 w-3" />
                            {t('video')}
                          </span>
                        </>
                      ) : (
                        <img
                          src={u.media_url}
                          alt={title}
                          className="h-full w-full object-cover"
                          loading="lazy"
                        />
                      )}
                    </div>
                    <div className="p-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-primary-600">
                        {project}
                      </p>
                      <h3 className="mt-1 text-lg font-semibold text-slate-900">{title}</h3>
                      {desc && <p className="mt-2 text-sm text-slate-600">{desc}</p>}
                      <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
                        <span>{localizeDigits(u.published_at)}</span>
                        {u.progress_percent != null && (
                          <span>
                            {t('progress')}: {localizeDigits(String(u.progress_percent))}%
                          </span>
                        )}
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
