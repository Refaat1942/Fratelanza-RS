import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  BarChart3, Building2, FileSpreadsheet, HandCoins, Headphones, Target, Users, Wallet, Table2,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { SortableTable } from '@/components/ui/SortableTable'
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
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [exporting, setExporting] = useState(false)

  const { data: catalog } = useQuery({
    queryKey: ['reports-catalog'],
    queryFn: async () => {
      const { data } = await api.get<ReportMeta[]>('/reports/catalog')
      return data
    },
  })

  const categories = useMemo(() => {
    const cats = new Set(catalog?.map((r) => r.category) ?? [])
    return ['all', ...Array.from(cats)]
  }, [catalog])

  const categoryCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const item of catalog ?? []) counts.set(item.category, (counts.get(item.category) ?? 0) + 1)
    return counts
  }, [catalog])

  const filteredCatalog = useMemo(() => {
    if (!catalog) return []
    if (category === 'all') return catalog
    return catalog.filter((r) => r.category === category)
  }, [catalog, category])

  const activeKey = selectedKey && filteredCatalog.some((r) => r.key === selectedKey)
    ? selectedKey
    : filteredCatalog[0]?.key ?? catalog?.[0]?.key ?? null

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', activeKey, search, sortKey, sortDir],
    queryFn: async () => {
      const { data } = await api.get<ReportData>(`/reports/${activeKey}`, {
        params: {
          ...(search ? { search } : {}),
          ...(sortKey ? { sort_by: sortKey, sort_order: sortDir } : {}),
        },
      })
      return data
    },
    enabled: !!activeKey,
  })

  const handleCategoryChange = (nextCategory: string) => {
    setCategory(nextCategory)
    setSearch('')
    setSortKey(null)
    const nextReport = nextCategory === 'all'
      ? catalog?.[0]
      : catalog?.find((item) => item.category === nextCategory)
    setSelectedKey(nextReport?.key ?? null)
  }

  const handleReportChange = (key: string) => {
    setSelectedKey(key)
    setSearch('')
    setSortKey(null)
  }

  const handleSortChange = (key: string, dir: 'asc' | 'desc') => {
    setSortKey(key)
    setSortDir(dir)
  }

  const handleExport = async () => {
    if (!activeKey) return
    setExporting(true)
    try {
      await downloadReport(activeKey, {
        ...(search ? { search } : {}),
        ...(sortKey ? { sort_by: sortKey, sort_order: sortDir } : {}),
      })
    } finally {
      setExporting(false)
    }
  }

  const reportName = report
    ? i18n.language === 'ar' ? report.name_ar : report.name_en
    : ''

  return (
    <div>
      <PageHeader
        title={t('reports')}
        subtitle={t('reports_subtitle')}
        icon={BarChart3}
        accentIndex={2}
      />

      <div className="grid-stagger mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-primary-50 p-2 text-primary-700"><Table2 className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('available_reports')}</p>
            <p className="text-xl font-bold text-slate-900">{catalog?.length ?? 0}</p>
          </div>
        </Card>
        {categories.filter((cat) => cat !== 'all').slice(0, 3).map((cat) => {
          const Icon = CATEGORY_ICONS[cat] ?? BarChart3
          return (
            <Card key={cat} className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-slate-100 p-2 text-slate-700"><Icon className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t(`report_cat_${cat}`)}</p>
                <p className="text-xl font-bold text-slate-900">{categoryCounts.get(cat) ?? 0}</p>
              </div>
            </Card>
          )
        })}
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => handleCategoryChange(cat)}
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
            <Card className="text-sm text-slate-500">{t('no_reports_available')}</Card>
          ) : filteredCatalog.map((item) => {
            const Icon = CATEGORY_ICONS[item.category] ?? BarChart3
            const name = i18n.language === 'ar' ? item.name_ar : item.name_en
            return (
              <button
                key={item.key}
                onClick={() => handleReportChange(item.key)}
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
            sortKey={sortKey}
            sortDir={sortDir}
            onSortChange={handleSortChange}
            onExport={handleExport}
            exportLoading={exporting}
          />
        </div>
      </div>
    </div>
  )
}
