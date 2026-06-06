import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { SortableTable } from '@/components/ui/SortableTable'
import { StatCard } from '@/components/ui/StatCard'
import { formatEGP } from '@/lib/currency'
import { downloadReport } from '@/lib/download'
import api from '@/lib/api'
import { cn } from '@/lib/utils'
import { Landmark, TrendingUp, Wallet, FileText } from 'lucide-react'

type FinanceTab = 'overview' | 'trial_balance' | 'profit_loss' | 'cash' | 'journal' | 'accounts'

export function FinancePage() {
  const { t, i18n } = useTranslation()
  const [tab, setTab] = useState<FinanceTab>('overview')
  const [exporting, setExporting] = useState(false)

  const reportKey: Record<FinanceTab, string | null> = {
    overview: null,
    trial_balance: 'finance_trial_balance',
    profit_loss: 'finance_profit_loss',
    cash: 'finance_cash_position',
    journal: 'finance_journal',
    accounts: null,
  }

  const { data: pl } = useQuery({
    queryKey: ['finance-pl'],
    queryFn: async () => (await api.get('/reports/finance_profit_loss')).data,
  })

  const { data: cash } = useQuery({
    queryKey: ['finance-cash'],
    queryFn: async () => (await api.get('/reports/finance_cash_position')).data,
  })

  const { data: accounts = [] } = useQuery({
    queryKey: ['finance-accounts'],
    queryFn: async () => (await api.get('/finance/accounts')).data,
  })

  const { data: report, isLoading } = useQuery({
    queryKey: ['finance-report', tab],
    queryFn: async () => (await api.get(`/reports/${reportKey[tab]}`)).data,
    enabled: !!reportKey[tab],
  })

  const tabs: { key: FinanceTab; label: string }[] = [
    { key: 'overview', label: t('overview') },
    { key: 'trial_balance', label: t('trial_balance') },
    { key: 'profit_loss', label: t('profit_loss') },
    { key: 'cash', label: t('cash_position') },
    { key: 'journal', label: t('journal_register') },
    { key: 'accounts', label: t('chart_of_accounts') },
  ]

  const salesLine = pl?.rows?.find((r: Record<string, unknown>) => r.line_item === 'Total Contracted Sales')
  const collectedLine = pl?.rows?.find((r: Record<string, unknown>) => r.line_item === 'Collections Received')
  const overdueLine = pl?.rows?.find((r: Record<string, unknown>) => r.line_item === 'Outstanding Overdue')
  const cashTotal = (cash?.rows ?? []).reduce((s: number, r: Record<string, unknown>) => s + Number(r.balance_egp ?? 0), 0)

  const handleExport = async () => {
    const key = reportKey[tab]
    if (!key) {
      await downloadReport('finance_profit_loss')
      return
    }
    setExporting(true)
    try { await downloadReport(key) } finally { setExporting(false) }
  }

  const accountRows = accounts.map((a: Record<string, unknown>) => ({
    code: a.code,
    name: i18n.language === 'ar' ? a.name_ar : a.name_en,
    type: a.account_type,
  }))

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">{t('finance')}</h1>
        <p className="text-sm text-slate-500">{t('finance_subtitle')}</p>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map(({ key, label }) => (
          <button key={key} onClick={() => setTab(key)} className={cn(
            'rounded-lg px-3 py-1.5 text-sm font-medium',
            tab === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
          )}>{label}</button>
        ))}
      </div>

      {tab === 'overview' && (
        <>
          <div className="mb-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard title={t('total_sales')} value={formatEGP(salesLine?.amount_egp)} icon={TrendingUp} />
            <StatCard title={t('total_collections')} value={formatEGP(collectedLine?.amount_egp)} icon={Wallet} color="bg-emerald-50 text-emerald-700" />
            <StatCard title={t('overdue_amount')} value={formatEGP(overdueLine?.amount_egp)} icon={FileText} color="bg-red-50 text-red-700" />
            <StatCard title={t('cash_position')} value={formatEGP(cashTotal)} icon={Landmark} color="bg-amber-50 text-amber-700" />
          </div>
          <SortableTable
            columns={pl?.columns ?? []}
            rows={(pl?.rows ?? []).map((r: Record<string, unknown>) => ({
              ...r,
              amount_egp: formatEGP(r.amount_egp as number),
            }))}
            onExport={handleExport}
            exportLoading={exporting}
          />
        </>
      )}

      {tab === 'accounts' && (
        <SortableTable
          columns={[
            { key: 'code', label_en: 'Code', label_ar: 'الكود' },
            { key: 'name', label_en: 'Account', label_ar: 'الحساب' },
            { key: 'type', label_en: 'Type', label_ar: 'النوع' },
          ]}
          rows={accountRows}
          onExport={() => downloadReport('finance_trial_balance')}
        />
      )}

      {reportKey[tab] && tab !== 'overview' && (
        <SortableTable
          columns={report?.columns ?? []}
          rows={(report?.rows ?? []).map((r: Record<string, unknown>) => {
            const formatted = { ...r }
            for (const k of Object.keys(formatted)) {
              if (k.includes('egp') || k.includes('amount') || k.includes('balance') || k.includes('debit') || k.includes('credit')) {
                if (typeof formatted[k] === 'number') formatted[k] = formatEGP(formatted[k] as number)
              }
            }
            return formatted
          })}
          loading={isLoading}
          total={report?.total}
          onExport={handleExport}
          exportLoading={exporting}
        />
      )}
    </div>
  )
}
