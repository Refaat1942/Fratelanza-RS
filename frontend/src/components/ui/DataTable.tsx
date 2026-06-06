import { Card } from './Card'
import { useTranslation } from 'react-i18next'

interface Column {
  key: string
  label: string
  render?: (row: Record<string, unknown>) => React.ReactNode
}

interface DataTableProps {
  title: string
  columns: Column[]
  data: Record<string, unknown>[]
  loading?: boolean
  actions?: React.ReactNode
}

export function DataTable({ title, columns, data, loading, actions }: DataTableProps) {
  const { t } = useTranslation()
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {actions}
      </div>
      <Card>
        {loading ? (
          <p className="text-slate-500">{t('loading')}</p>
        ) : data.length === 0 ? (
          <p className="text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  {columns.map((col) => (
                    <th key={col.key} className="pb-3 text-start font-medium">{col.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={i} className="border-b border-slate-100">
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
