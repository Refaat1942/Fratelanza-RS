import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Download, FileBarChart } from 'lucide-react'
import api from '@/lib/api'
import { apiErrorMessage } from '@/lib/apiError'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { ErrorNote } from '@/components/ui/FormFields'
import { usePermissionsStore } from '@/stores/permissionsStore'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { cn } from '@/lib/utils'

type Meta = { key: string; name_ar: string; name_en: string; sensitive: boolean }
type Result = { key: string; name_ar: string; name_en: string; rows: Record<string, unknown>[]; totals: Record<string, number> }

const MONEY_HINTS = ['amount', 'collected', 'outstanding', 'billed', 'due', 'paid', 'rent', 'commission', 'expenses', 'net', 'gross',
  'revenue', 'profit', 'remaining', 'owed', 'refunded', 'payable', 'income', 'payroll', 'adjustments', 'overdue']

export function ReReportsPanel() {
  const { t, i18n } = useTranslation()
  const { formatEGP, formatNumber } = useFormatNumber()
  const can = usePermissionsStore((s) => s.can)
  const [key, setKey] = useState<string | null>(new URLSearchParams(window.location.search).get('report'))
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [error, setError] = useState<string | null>(null)
  const catalog = useQuery({ queryKey: ['re-report-catalog'], queryFn: async () => (await api.get<Meta[]>('/re-reports/catalog')).data })
  const active = key ?? catalog.data?.[0]?.key ?? null
  const params = new URLSearchParams()
  if (from) params.set('date_from', from)
  if (to) params.set('date_to', to)
  const report = useQuery({
    queryKey: ['re-report', active, from, to], enabled: !!active,
    queryFn: async () => (await api.get<Result>(`/re-reports/${active}?${params.toString()}`)).data,
  })

  const exportXlsx = async () => {
    setError(null)
    try {
      const { data } = await api.get(`/re-reports/${active}/export?format=xlsx&${params.toString()}`, { responseType: 'blob' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(data as Blob)
      a.download = `${active}.xlsx`
      a.click()
    } catch (err) { setError(apiErrorMessage(err, t)) }
  }

  const fmt = (col: string, v: unknown) => {
    if (typeof v === 'number') return MONEY_HINTS.some((h) => col.includes(h)) ? formatEGP(v) : formatNumber(v)
    if (typeof v === 'boolean') return v ? t('re.yes') : t('re.no')
    if (col === 'line') return t(`re.pl.${v}`, { defaultValue: String(v) })
    if (col === 'status' || col === 'occupancy' || col === 'approval_status' || col === 'payment_status') return t(`re.status.${v}`, { defaultValue: String(v ?? '') })
    return String(v ?? '—')
  }

  if (!catalog.data?.length) return null
  const columns = report.data?.rows[0] ? Object.keys(report.data.rows[0]) : []

  return (
    <div className="grid gap-6 lg:grid-cols-4">
      <div className="space-y-2 lg:col-span-1">
        {catalog.data.map((m) => (
          <button key={m.key} onClick={() => setKey(m.key)}
            className={cn('flex w-full items-center gap-2 rounded-lg px-3 py-2 text-start text-sm', active === m.key ? 'bg-primary-700 text-white' : 'bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50')}>
            <FileBarChart className="h-4 w-4 shrink-0" />{i18n.language === 'ar' ? m.name_ar : m.name_en}
          </button>
        ))}
      </div>
      <Card className="lg:col-span-3">
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <div className="w-40"><Input type="date" label={t('re.fields.date_from')} value={from} onChange={(e) => setFrom(e.target.value)} /></div>
          <div className="w-40"><Input type="date" label={t('re.fields.date_to')} value={to} onChange={(e) => setTo(e.target.value)} /></div>
          {can('reports', 'export') && <Button variant="secondary" onClick={exportXlsx}><Download className="me-2 h-4 w-4" />{t('export_excel')}</Button>}
        </div>
        <ErrorNote message={error} />
        {report.isLoading ? <p className="text-slate-500">{t('loading')}</p> : !report.data?.rows.length ? (
          <p className="rounded-lg bg-slate-50 p-6 text-center text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="table-head-gradient"><tr>{columns.map((c) => <th key={c} className="px-3 py-2 text-start">{t(`re.col.${c}`, { defaultValue: c })}</th>)}</tr></thead>
              <tbody>
                {report.data.rows.map((row, i) => (
                  <tr key={i} className="border-b border-slate-100">{columns.map((c) => <td key={c} className="px-3 py-2">{fmt(c, row[c])}</td>)}</tr>
                ))}
              </tbody>
              {Object.keys(report.data.totals).length > 0 && active !== 'profit_loss' && (
                <tfoot className="bg-slate-50 font-semibold"><tr>{columns.map((c, i) => (
                  <td key={c} className="px-3 py-2">{c in report.data!.totals ? fmt(c, report.data!.totals[c]) : i === 0 ? t('re.total') : ''}</td>
                ))}</tr></tfoot>
              )}
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
