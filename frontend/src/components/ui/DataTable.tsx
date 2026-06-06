import { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Card } from './Card'
import { PageHeader } from './PageHeader'
import { LoadingState } from './LoadingState'
import { EmptyState } from './EmptyState'
import { useTranslation } from 'react-i18next'
import { ArrowDown, ArrowUp, ArrowUpDown, Download, Search, Table2 } from 'lucide-react'
import { Button } from './Button'
import { exportRowsToExcel } from '@/lib/exportTable'
import { accentForPath } from '@/lib/pageAccent'
import { cn } from '@/lib/utils'

interface Column {
  key: string
  label: string
  render?: (row: Record<string, unknown>) => React.ReactNode
  sortable?: boolean
}

interface DataTableProps {
  title: string
  columns: Column[]
  data: Record<string, unknown>[]
  loading?: boolean
  actions?: React.ReactNode
  rowActions?: (row: Record<string, unknown>) => React.ReactNode
  searchable?: boolean
  exportFilename?: string
  subtitle?: string
  emptyActionLabel?: string
  onEmptyAction?: () => void
}

function StatusCell({ value }: { value: unknown }) {
  const str = String(value ?? '').toLowerCase()
  const cls =
    ['active', 'paid', 'available', 'completed'].some((s) => str.includes(s)) ? 'status-active'
    : ['pending', 'trial', 'partial'].some((s) => str.includes(s)) ? 'status-pending'
    : ['overdue', 'suspended', 'expired', 'cancelled'].some((s) => str.includes(s)) ? 'status-overdue'
    : ''
  if (!cls) return <>{String(value ?? '-')}</>
  return <span className={cls}>{String(value)}</span>
}

export function DataTable({ title, columns, data, loading, actions, rowActions, searchable = true, exportFilename, subtitle, emptyActionLabel, onEmptyAction }: DataTableProps) {
  const { t } = useTranslation()
  const { pathname } = useLocation()
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const filtered = useMemo(() => {
    let rows = [...data]
    if (search) {
      const q = search.toLowerCase()
      rows = rows.filter((row) =>
        columns.some((col) => {
          const val = col.render ? String(col.render(row)) : String(row[col.key] ?? '')
          return val.toLowerCase().includes(q)
        }),
      )
    }
    if (sortKey) {
      rows.sort((a, b) => {
        const av = a[sortKey]
        const bv = b[sortKey]
        if (typeof av === 'number' && typeof bv === 'number') {
          return sortDir === 'asc' ? av - bv : bv - av
        }
        const cmp = String(av ?? '').localeCompare(String(bv ?? ''))
        return sortDir === 'asc' ? cmp : -cmp
      })
    }
    return rows
  }, [data, search, sortKey, sortDir, columns])

  const toggleSort = (key: string) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('asc') }
  }

  const headerActions = (
    <>
      {exportFilename && data.length > 0 && (
        <Button variant="secondary" onClick={() => exportRowsToExcel(filtered, exportFilename)}>
          <Download className="me-2 h-4 w-4" />{t('export_excel')}
        </Button>
      )}
      {actions}
    </>
  )

  return (
    <div>
      <PageHeader
        title={title}
        subtitle={subtitle}
        icon={Table2}
        accentIndex={accentForPath(pathname)}
        actions={headerActions}
      />
      <Card>
        {searchable && (
          <div className="relative mb-4 max-w-md">
            <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-primary-400" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('search_table')}
              className="input-field ps-10"
            />
          </div>
        )}
        {loading ? (
          <LoadingState />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={t('no_data')}
            description={t('no_data_help')}
            actionLabel={emptyActionLabel ?? (onEmptyAction ? t('add') : undefined)}
            onAction={onEmptyAction}
          />
        ) : (
          <div className="overflow-x-auto rounded-lg">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head-gradient border-b border-slate-200">
                  {columns.map((col) => (
                    <th key={col.key} className="px-3 py-3 text-start" scope="col">
                      {col.sortable !== false ? (
                        <button
                          onClick={() => toggleSort(col.key)}
                          className={cn(
                            'inline-flex items-center gap-1 transition-colors hover:text-primary-800',
                            sortKey === col.key && 'text-primary-800',
                          )}
                        >
                          {col.label}
                          {sortKey === col.key ? (
                            sortDir === 'asc' ? <ArrowUp className="h-3.5 w-3.5" /> : <ArrowDown className="h-3.5 w-3.5" />
                          ) : (
                            <ArrowUpDown className="h-3.5 w-3.5 opacity-40" />
                          )}
                        </button>
                      ) : col.label}
                    </th>
                  ))}
                  {rowActions && <th className="px-3 py-3 text-start" scope="col">{t('actions')}</th>}
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => (
                  <tr
                    key={String(row.id ?? i)}
                    className="table-row-animate border-b border-slate-100"
                    style={{ animationDelay: `${Math.min(i * 0.04, 0.6)}s` }}
                  >
                    {columns.map((col) => (
                      <td key={col.key} className="px-3 py-3">
                        {col.render
                          ? col.render(row)
                          : col.key === 'status'
                            ? <StatusCell value={row[col.key]} />
                            : String(row[col.key] ?? '-')}
                      </td>
                    ))}
                    {rowActions && <td className="px-3 py-3">{rowActions(row)}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
