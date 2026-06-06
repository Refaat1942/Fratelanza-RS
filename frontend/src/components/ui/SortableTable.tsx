import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowDown, ArrowUp, ArrowUpDown, Download, Search } from 'lucide-react'
import { Card } from './Card'
import { Button } from './Button'
import { cn } from '@/lib/utils'

export interface TableColumn {
  key: string
  label_en: string
  label_ar: string
  sortable?: boolean
}

interface SortableTableProps {
  columns: TableColumn[]
  rows: Record<string, unknown>[]
  loading?: boolean
  onExport?: () => void
  exportLoading?: boolean
  searchPlaceholder?: string
  onSearchChange?: (value: string) => void
  searchValue?: string
  total?: number
}

export function SortableTable({
  columns,
  rows,
  loading,
  onExport,
  exportLoading,
  searchPlaceholder,
  onSearchChange,
  searchValue = '',
  total,
}: SortableTableProps) {
  const { t, i18n } = useTranslation()
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [localSearch, setLocalSearch] = useState('')

  const search = onSearchChange ? searchValue : localSearch
  const setSearch = onSearchChange ?? setLocalSearch

  const sortedRows = useMemo(() => {
    let data = [...rows]
    if (!onSearchChange && search) {
      const q = search.toLowerCase()
      data = data.filter((row) =>
        Object.values(row).some((v) => v != null && String(v).toLowerCase().includes(q)),
      )
    }
    if (sortKey) {
      data.sort((a, b) => {
        const av = a[sortKey]
        const bv = b[sortKey]
        if (av == null && bv == null) return 0
        if (av == null) return 1
        if (bv == null) return -1
        if (typeof av === 'number' && typeof bv === 'number') {
          return sortDir === 'asc' ? av - bv : bv - av
        }
        const cmp = String(av).localeCompare(String(bv))
        return sortDir === 'asc' ? cmp : -cmp
      })
    }
    return data
  }, [rows, sortKey, sortDir, search, onSearchChange])

  const toggleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const label = (col: TableColumn) => (i18n.language === 'ar' ? col.label_ar : col.label_en)

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="relative min-w-[200px] flex-1 max-w-md">
          <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={searchPlaceholder ?? t('search_table')}
            className="input-field ps-10"
          />
        </div>
        <div className="flex items-center gap-3">
          {total != null && (
            <span className="text-sm text-slate-500">{t('total_records')}: {total}</span>
          )}
          {onExport && (
            <Button onClick={onExport} loading={exportLoading} variant="secondary">
              <Download className="me-2 h-4 w-4" />
              {t('export_excel')}
            </Button>
          )}
        </div>
      </div>
      {loading ? (
        <p className="text-slate-500">{t('loading')}</p>
      ) : sortedRows.length === 0 ? (
        <p className="text-slate-500">{t('no_data')}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head-gradient">
                {columns.map((col) => (
                  <th key={col.key} className="pb-3 text-start">
                    {col.sortable !== false ? (
                      <button
                        onClick={() => toggleSort(col.key)}
                        className={cn(
                          'inline-flex items-center gap-1 hover:text-slate-700',
                          sortKey === col.key && 'text-primary-700',
                        )}
                      >
                        {label(col)}
                        {sortKey === col.key ? (
                          sortDir === 'asc' ? <ArrowUp className="h-3.5 w-3.5" /> : <ArrowDown className="h-3.5 w-3.5" />
                        ) : (
                          <ArrowUpDown className="h-3.5 w-3.5 opacity-40" />
                        )}
                      </button>
                    ) : (
                      label(col)
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, i) => (
                <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                  {columns.map((col) => (
                    <td key={col.key} className="py-3">
                      {row[col.key] != null ? String(row[col.key]) : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}
