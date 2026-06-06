import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Phone, Plus, CheckCircle } from 'lucide-react'
import { SortableTable } from '@/components/ui/SortableTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { ReminderFormModal } from '@/components/forms/ReminderFormModal'
import { exportRowsToExcel } from '@/lib/exportTable'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

export function FollowUpsPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState<'all' | 'today' | 'overdue'>('all')

  const { data: reminders = [], isLoading } = useQuery({
    queryKey: ['reminders', filter],
    queryFn: async () => {
      const params = filter === 'today' ? { due_today: true } : undefined
      return (await api.get('/reminders', { params })).data
    },
  })

  const { data: summary } = useQuery({
    queryKey: ['reminders-summary'],
    queryFn: async () => (await api.get('/reminders/summary')).data,
  })

  const filtered = filter === 'overdue'
    ? reminders.filter((r: Record<string, unknown>) => r.status === 'overdue')
    : reminders

  const updateStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      await api.patch(`/reminders/${id}`, { status })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reminders'] })
      qc.invalidateQueries({ queryKey: ['reminders-summary'] })
    },
  })

  const statusColor: Record<string, string> = {
    pending: 'bg-amber-50 text-amber-700',
    overdue: 'bg-red-50 text-red-700',
    completed: 'bg-emerald-50 text-emerald-700',
    cancelled: 'bg-slate-100 text-slate-600',
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('follow_ups')}</h1>
          <p className="text-sm text-slate-500">{t('follow_ups_help')}</p>
        </div>
        <Button onClick={() => setOpen(true)}><Plus className="me-2 h-4 w-4" />{t('schedule_call')}</Button>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-800">{t('calls_today')}</p>
          <p className="text-2xl font-bold text-amber-900">{summary?.today ?? 0}</p>
        </div>
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">{t('overdue')}</p>
          <p className="text-2xl font-bold text-red-900">{summary?.overdue ?? 0}</p>
        </div>
        <div className="rounded-xl border border-primary-200 bg-primary-50 p-4">
          <p className="text-sm text-primary-800">{t('pending')}</p>
          <p className="text-2xl font-bold text-primary-900">{summary?.pending ?? 0}</p>
        </div>
      </div>

      <div className="mb-4 flex gap-2">
        {(['all', 'today', 'overdue'] as const).map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={cn(
            'rounded-lg px-3 py-1.5 text-sm font-medium capitalize',
            filter === f ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
          )}>{t(`filter_${f}`)}</button>
        ))}
      </div>

      {!isLoading && filtered.length === 0 ? (
        <EmptyState
          icon={<Phone className="h-10 w-10" />}
          title={t('no_reminders_yet')}
          description={t('no_reminders_help')}
          actionLabel={t('schedule_call')}
          onAction={() => setOpen(true)}
        />
      ) : (
        <div className="space-y-2">
          {filtered.map((r: Record<string, unknown>) => (
            <div key={r.id as number} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-primary-600" />
                <div>
                  <p className="font-medium text-slate-900">{r.title as string}</p>
                  <p className="text-xs text-slate-500">
                    {r.due_date as string} {r.due_time as string}
                    {r.linked_to ? ` · ${r.linked_to as string}` : ''}
                    {' · '}{String(r.reminder_type).replace('_', ' ')}
                  </p>
                </div>
                <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', statusColor[r.status as string] ?? '')}>
                  {r.status as string}
                </span>
              </div>
              {r.status !== 'completed' && (
                <Button variant="secondary" onClick={() => updateStatus.mutate({ id: r.id as number, status: 'completed' })}>
                  <CheckCircle className="me-1 h-4 w-4" />{t('mark_done')}
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {filtered.length > 0 && (
        <div className="mt-6">
          <SortableTable
            columns={[
              { key: 'title', label_en: 'Title', label_ar: 'العنوان' },
              { key: 'linked_to', label_en: 'Customer/Lead', label_ar: 'العميل' },
              { key: 'reminder_type', label_en: 'Type', label_ar: 'النوع' },
              { key: 'due_date', label_en: 'Date', label_ar: 'التاريخ' },
              { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
            ]}
            rows={filtered.map((r: Record<string, unknown>) => ({
              ...r,
              reminder_type: String(r.reminder_type).replace('_', ' '),
              linked_to: r.linked_to || '-',
            }))}
            loading={isLoading}
            onExport={() => exportRowsToExcel(reminders, 'reminders')}
          />
        </div>
      )}

      <ReminderFormModal open={open} onClose={() => { setOpen(false); qc.invalidateQueries({ queryKey: ['reminders'] }) }} />
    </div>
  )
}
