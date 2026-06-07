import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  BarChart3, Building2, FileSpreadsheet, HandCoins, Headphones, Target, Users, Wallet,
  HardHat, Shield, AlertCircle,
} from 'lucide-react'
import { SortableTable } from '@/components/ui/SortableTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
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
  operations: HardHat,
  admin: Shield,
}

export function ReportsPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const reportFromUrl = searchParams.get('report')
  const [selectedKey, setSelectedKey] = useState<string | null>(reportFromUrl)
  const [category, setCategory] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [exporting, setExporting] = useState(false)

  const { data: catalog, isLoading: catalogLoading, isError: catalogError, refetch: refetchCatalog } = useQuery({
    queryKey: ['reports-catalog'],
    queryFn: async () => {
      const { data } = await api.get<ReportMeta[]>('/reports/catalog')
      return data
    },
  })

  useEffect(() => {
    if (reportFromUrl) setSelectedKey(reportFromUrl)
  }, [reportFromUrl])

  const activeKey = selectedKey ?? catalog?.[0]?.key ?? null

  const { data: report, isLoading: reportLoading, refetch: refetchReport } = useQuery({
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
    return ['all', ...Array.from(cats).sort()]
  }, [catalog])

  const filteredCatalog = useMemo(() => {
    if (!catalog) return []
    if (category === 'all') return catalog
    return catalog.filter((r) => r.category === category)
  }, [catalog, category])

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const r of catalog ?? []) {
      counts[r.category] = (counts[r.category] ?? 0) + 1
    }
    return counts
  }, [catalog])

  const handleExport = async () => {
    if (!activeKey) return
    setExporting(true)
    try {
      await downloadReport(activeKey, search ? { search } : undefined)
    } finally {
      setExporting(false)
    }
  }

  const reloadReports = () => {
    refetchCatalog()
    if (activeKey) refetchReport()
  }

  const reportName = report
    ? i18n.language === 'ar' ? report.name_ar : report.name_en
    : ''

  if (catalogError) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">{t('reports')}</h1>
          <p className="mt-1 text-sm text-slate-500">{t('reports_subtitle')}</p>
        </div>
        <EmptyState
          icon={<AlertCircle className="h-12 w-12" />}
          title={t('reports_load_error')}
          description={t('reports_load_error_help')}
          actionLabel={t('reload_dashboard')}
          onAction={reloadReports}
        />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('reports')}</h1>
          <p className="mt-1 text-sm text-slate-500">{t('reports_subtitle')}</p>
        </div>
        <Button variant="secondary" onClick={reloadReports} loading={catalogLoading}>
          <BarChart3 className="me-2 h-4 w-4" />
          {t('reload_reports')}
        </Button>
      </div>

      {!catalogLoading && catalog && catalog.length > 0 && (
        <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-sm text-slate-500">{t('total_reports')}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{catalog.length}</p>
          </div>
          {Object.entries(categoryCounts).slice(0, 3).map(([cat, count]) => {
            const Icon = CATEGORY_ICONS[cat] ?? BarChart3
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className="rounded-xl border border-slate-200 bg-white p-4 text-start transition hover:border-primary-300 hover:bg-primary-50/50"
              >
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-primary-600" />
                  <p className="text-sm text-slate-500">{t(`report_cat_${cat}`, cat)}</p>
                </div>
                <p className="mt-1 text-2xl font-bold text-slate-900">{count}</p>
              </button>
            )
          })}
        </div>
      )}

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
            {cat === 'all' ? t('all_reports') : t(`report_cat_${cat}`, cat)}
          </button>
        ))}
      </div>

      {catalogLoading ? (
        <p className="text-slate-500">{t('loading')}</p>
      ) : !catalog || catalog.length === 0 ? (
        <EmptyState
          icon={<BarChart3 className="h-12 w-12" />}
          title={t('no_reports_available')}
          description={t('no_reports_available_help')}
          actionLabel={t('load_demo_data')}
          onAction={() => navigate('/dashboard')}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-4">
          <div className="max-h-[70vh] space-y-2 overflow-y-auto lg:col-span-1">
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
            <div className="mb-4 flex items-center justify-between gap-4">
              <h2 className="text-lg font-semibold text-slate-900">{reportName}</h2>
              {report && (
                <span className="text-sm text-slate-500">
                  {t('report_rows_count', { count: report.total })}
                </span>
              )}
            </div>
            <SortableTable
              columns={report?.columns ?? []}
              rows={report?.rows ?? []}
              loading={reportLoading}
              total={report?.total}
              searchValue={search}
              onSearchChange={setSearch}
              onExport={handleExport}
              exportLoading={exporting}
            />
          </div>
        </div>
      )}
    </div>
  )
}
