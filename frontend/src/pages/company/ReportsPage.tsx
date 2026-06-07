import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  BarChart3, Building2, FileSpreadsheet, HandCoins, Headphones, Target, Users, Wallet, RefreshCw, Table2, Layers,
} from 'lucide-react'
import { SortableTable } from '@/components/ui/SortableTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { LoadingState } from '@/components/ui/LoadingState'
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
}

export function ReportsPage() {
  const { t, i18n } = useTranslation()
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
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

  const activeKey = selectedKey ?? catalog?.[0]?.key ?? null
  const activeMeta = catalog?.find((item) => item.key === activeKey)

  const { data: report, isLoading, isError: reportError, refetch: refetchReport } = useQuery({
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

  const reportStats = useMemo(() => ({
    reports: catalog?.length ?? 0,
    categories: Math.max(categories.length - 1, 0),
    rows: report?.total ?? report?.rows.length ?? 0,
    columns: report?.columns.length ?? 0,
  }), [catalog?.length, categories.length, report])

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
    } catch {
      alert(t('export_failed'))
    } finally {
      setExporting(false)
    }
  }

  const reportName = report
    ? i18n.language === 'ar' ? report.name_ar : report.name_en
    : activeMeta
      ? i18n.language === 'ar' ? activeMeta.name_ar : activeMeta.name_en
      : ''

  return (
    <div>
      <PageHeader
        title={t('reports')}
        subtitle={t('reports_subtitle')}
        icon={BarChart3}
        accentIndex={5}
        actions={
          <Button variant="secondary" onClick={() => refetchCatalog()} loading={catalogLoading}>
            <RefreshCw className="me-2 h-4 w-4" />
            {t('refresh_reports')}
          </Button>
        }
      />

      {catalogLoading ? (
        <LoadingState />
      ) : catalogError ? (
        <EmptyState
          icon={<BarChart3 className="h-10 w-10" />}
          title={t('reports_unavailable')}
          description={t('reports_load_error')}
          actionLabel={t('retry')}
          onAction={() => refetchCatalog()}
        />
      ) : !catalog?.length ? (
        <EmptyState
          icon={<BarChart3 className="h-10 w-10" />}
          title={t('no_reports_configured')}
          description={t('no_reports_configured_help')}
          actionLabel={t('refresh_reports')}
          onAction={() => refetchCatalog()}
        />
      ) : (
        <>
          <div className="grid-stagger mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-primary-50 p-2 text-primary-700"><FileSpreadsheet className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t('available_reports')}</p>
                <p className="text-xl font-bold">{reportStats.reports}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-violet-50 p-2 text-violet-700"><Layers className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t('report_categories')}</p>
                <p className="text-xl font-bold">{reportStats.categories}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-emerald-50 p-2 text-emerald-700"><Table2 className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t('current_report_rows')}</p>
                <p className="text-xl font-bold">{reportStats.rows}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-amber-50 p-2 text-amber-700"><BarChart3 className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t('current_report_columns')}</p>
                <p className="text-xl font-bold">{reportStats.columns}</p>
              </div>
            </Card>
          </div>

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
              {filteredCatalog.length === 0 ? (
                <Card className="p-4 text-sm text-slate-500">{t('no_reports_in_category')}</Card>
              ) : filteredCatalog.map((item) => {
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
              {reportError ? (
                <EmptyState
                  icon={<FileSpreadsheet className="h-10 w-10" />}
                  title={t('report_unavailable')}
                  description={t('report_load_error')}
                  actionLabel={t('retry')}
                  onAction={() => refetchReport()}
                />
              ) : (
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
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
