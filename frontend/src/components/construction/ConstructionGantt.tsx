import { useTranslation } from 'react-i18next'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { cn } from '@/lib/utils'

export interface GanttRow {
  id: string
  entity_id: number
  type: 'phase' | 'task'
  phase_id: number
  label_ar: string
  label_en: string
  start: string
  end: string
  progress_percent: number
  depends_on_task_id?: number | null
  status?: string
  contractor?: string
}

interface ConstructionGanttProps {
  rows: GanttRow[]
  rangeStart: string
  rangeEnd: string
  loading?: boolean
}

function parseDate(s: string): number {
  return new Date(s.slice(0, 10)).getTime()
}

function monthLabels(start: string, end: string): { label: string; left: number }[] {
  const s = new Date(start.slice(0, 10))
  const e = new Date(end.slice(0, 10))
  const total = parseDate(end) - parseDate(start) || 1
  const labels: { label: string; left: number }[] = []
  const cursor = new Date(s.getFullYear(), s.getMonth(), 1)
  while (cursor <= e) {
    const left = ((cursor.getTime() - parseDate(start)) / total) * 100
    labels.push({
      label: cursor.toLocaleDateString(undefined, { month: 'short', year: '2-digit' }),
      left: Math.max(0, Math.min(100, left)),
    })
    cursor.setMonth(cursor.getMonth() + 1)
  }
  return labels
}

export function ConstructionGantt({ rows, rangeStart, rangeEnd, loading }: ConstructionGanttProps) {
  const { t, i18n } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const totalMs = parseDate(rangeEnd) - parseDate(rangeStart) || 1

  const barStyle = (start: string, end: string) => {
    const left = ((parseDate(start) - parseDate(rangeStart)) / totalMs) * 100
    const width = ((parseDate(end) - parseDate(start)) / totalMs) * 100
    return {
      left: `${Math.max(0, left)}%`,
      width: `${Math.max(2, Math.min(100 - left, width))}%`,
    }
  }

  const headers = monthLabels(rangeStart, rangeEnd)

  if (loading) {
    return <p className="text-slate-500">{t('loading')}</p>
  }

  if (!rows.length) {
    return <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-slate-500">{t('no_schedule_data')}</p>
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="min-w-[720px]">
        <div className="grid grid-cols-[220px_1fr] border-b border-slate-200 bg-slate-50 text-xs font-medium text-slate-500">
          <div className="px-4 py-3">{t('timeline_item')}</div>
          <div className="relative h-10 border-s border-slate-200">
            {headers.map((h) => (
              <span key={h.label + h.left} className="absolute top-3 -translate-x-1/2 text-[10px]" style={{ left: `${h.left}%` }}>
                {h.label}
              </span>
            ))}
          </div>
        </div>

        {rows.map((row) => {
          const label = i18n.language === 'ar' ? row.label_ar : row.label_en
          const style = barStyle(row.start, row.end)
          const isPhase = row.type === 'phase'
          return (
            <div key={row.id} className="grid grid-cols-[220px_1fr] border-b border-slate-100 last:border-0">
              <div className={cn('flex flex-col justify-center px-4 py-3', !isPhase && 'ps-8')}>
                <span className={cn('text-sm', isPhase ? 'font-semibold text-slate-900' : 'text-slate-700')}>{label}</span>
                {!isPhase && row.contractor && (
                  <span className="text-xs text-slate-400">{row.contractor}</span>
                )}
              </div>
              <div className="relative border-s border-slate-100 py-3 pe-4">
                <div className="relative h-8 rounded-md bg-slate-100/80">
                  <div
                    className={cn(
                      'absolute top-1 h-6 rounded-md shadow-sm transition-all',
                      isPhase ? 'bg-primary-500/90' : 'bg-cyan-500/90',
                    )}
                    style={style}
                    title={`${row.start} → ${row.end}`}
                  >
                    <div
                      className="h-full rounded-md bg-black/20"
                      style={{ width: `${row.progress_percent}%` }}
                    />
                  </div>
                  <span className="absolute end-2 top-1/2 -translate-y-1/2 text-[10px] font-medium text-slate-600">
                    {formatInteger(row.progress_percent)}%
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
