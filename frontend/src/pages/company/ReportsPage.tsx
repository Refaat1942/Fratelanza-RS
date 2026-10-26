import { useMemo, useState } from 'react'
import i18n from '@/i18n'
import { Tabs } from '@/components/ui/FormFields'
import { ReReportsPanel } from '@/components/reports/ReReportsPanel'
import { useAuthStore } from '@/stores/authStore'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  BarChart3, Building2, FileSpreadsheet, HandCoins, Headphones, Target, Users, Wallet,
} from 'lucide-react'
import { SortableTable } from '@/components/ui/SortableTable'
import { AIReportingPanel } from '@/components/reports/AIReportingPanel'
import { downloadReport } from '@/lib/download'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

interface ReportMeta {
  key: string
  category: string
  name_en: string
  name_ar: string
}

interface ReportData {
  key: string
  name_en: string
  name_ar: string
  category: string
  total: number
  columns: { key: string; label_en: string; label_ar: string; sortable?: boolean }[]
  rows: Record<string, unknown>[]
}

const CATEGORY_ICONS: Record<string, typeof BarChart3> = {
  inventory: Building2,
  sales: FileSpreadsheet,
  collections: HandCoins,
  crm: Target,
  brokers: Users,
  service: Headphones,
  platform: BarChart3,
  finance: Wallet,
  hr: Users,
}

export function ReportsPage() {
  const isSuperAdmin = useAuthStore((s) => !!s.user?.is_super_admin)
  const [view, setView] = useState(new URLSearchParams(window.location.search).get('tab') === 're' ? 're' : 'erp')
  return (
    <div>
      {!isSuperAdmin && (
        <Tabs active={view} onChange={setView} tabs={[
          { key: 'erp', label: i18n.t('re.reports.erp') },
          { key: 're', label: i18n.t('re.reports.property') },
        ]} />
      )}
      {view === 're' && !isSuperAdmin ? <ReReportsPanel /> : <ErpReports />}
    </div>
  )
}

function ErpReports() {
  const { t, i18n } = useTranslation()
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [category, setCategory] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [exporting, setExporting] = useState(false)

  const { data: catalog } = useQuery({
    queryKey: ['reports-catalog'],
    queryFn: async () => {
      const { data } = await api.get<ReportMeta[]>('/reports/catalog')
      return data
    },
  })

  const activeKey = selectedKey ?? catalog?.[0]?.key ?? null

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', activeKey, search],
    queryFn: async () => {
      const { data } = await api.get<ReportData>(`/reports/${activeKey}`, {
        params: search ? { search } : undefined,
      })
      return data
    },
    enabled: !!activeKey,
  })

  const categories = useMemo(() => {
    const cats = new Set(catalog?.map((r) => r.category) ?? [])
    return ['all', ...Array.from(cats)]
  }, [catalog])

  const filteredCatalog = useMemo(() => {
    if (!catalog) return []
    if (category === 'all') return catalog
    return catalog.filter((r) => r.category === category)
  }, [catalog, category])

  const handleExport = async () => {
    if (!activeKey) return
    setExporting(true)
    try {
      await downloadReport(activeKey, search ? { search } : undefined)
    } finally {
      setExporting(false)
    }
  }

  const reportName = report
    ? i18n.language === 'ar' ? report.name_ar : report.name_en
    : ''

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">{t('reports')}</h1>
        <p className="mt-1 text-sm text-slate-500">{t('reports_subtitle')}</p>
      </div>

      <AIReportingPanel activeReportKey={activeKey} activeReportName={reportName} />

      <div className="mb-4 flex flex-wrap gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={cn(
              'rounded-lg px-3 py-1.5 text-sm font-medium capitalize',
              category === cat
                ? 'bg-primary-700 text-white'
                : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50',
            )}
          >
            {cat === 'all' ? t('all_reports') : t(`report_cat_${cat}`)}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="space-y-2 lg:col-span-1">
          {filteredCatalog.map((item) => {
            const Icon = CATEGORY_ICONS[item.category] ?? BarChart3
            const name = i18n.language === 'ar' ? item.name_ar : item.name_en
            return (
              <button
                key={item.key}
                onClick={() => setSelectedKey(item.key)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-xl border p-3 text-start text-sm transition',
                  activeKey === item.key
                    ? 'border-primary-300 bg-primary-50 text-primary-800'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300',
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="font-medium">{name}</span>
              </button>
            )
          })}
        </div>

        <div className="lg:col-span-3">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">{reportName}</h2>
          <SortableTable
            columns={report?.columns ?? []}
            rows={report?.rows ?? []}
            loading={isLoading}
            total={report?.total}
            searchValue={search}
            onSearchChange={setSearch}
            onExport={handleExport}
            exportLoading={exporting}
          />
        </div>
      </div>
    </div>
  )
}
