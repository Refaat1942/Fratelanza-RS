import { useMemo, useState } from 'react'
import { Card } from './Card'
import { useTranslation } from 'react-i18next'
import { ArrowDown, ArrowUp, ArrowUpDown, Search } from 'lucide-react'
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
  searchable?: boolean
}

export function DataTable({ title, columns, data, loading, actions, searchable = true }: DataTableProps) {
  const { t } = useTranslation()
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

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {actions}
      </div>
      <Card>
        {searchable && (
          <div className="relative mb-4 max-w-md">
            <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
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
          <p className="text-slate-500">{t('loading')}</p>
        ) : filtered.length === 0 ? (
          <p className="text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  {columns.map((col) => (
                    <th key={col.key} className="pb-3 text-start font-medium">
                      {col.sortable !== false ? (
                        <button
                          onClick={() => toggleSort(col.key)}
                          className={cn(
                            'inline-flex items-center gap-1 hover:text-slate-700',
                            sortKey === col.key && 'text-primary-700',
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
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => (
                  <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                    {columns.map((col) => (
                      <td key={col.key} className="py-3">
                        {col.render ? col.render(row) : String(row[col.key] ?? '-')}
                      </td>
                    ))}
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
