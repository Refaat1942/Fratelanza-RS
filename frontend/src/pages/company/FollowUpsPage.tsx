import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Phone, Plus, CheckCircle } from 'lucide-react'
import { SortableTable } from '@/components/ui/SortableTable'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { exportRowsToExcel } from '@/lib/exportTable'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

export function FollowUpsPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState<'all' | 'today' | 'overdue'>('all')
  const [form, setForm] = useState({
    title: '', reminder_type: 'call', due_date: '', due_time: '10:00', notes: '',
  })

  const { data: reminders = [], isLoading } = useQuery({
    queryKey: ['reminders', filter],
    queryFn: async () => {
      const params = filter === 'today' ? { due_today: true } : undefined
      return (await api.get('/reminders', { params })).data
    },
  })

  const filtered = filter === 'overdue'
    ? reminders.filter((r: Record<string, unknown>) => r.status === 'overdue')
    : reminders

  const updateStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      await api.patch(`/reminders/${id}`, { status })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reminders'] }),
  })

  const createReminder = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.post('/reminders', form)
    setOpen(false)
    setForm({ title: '', reminder_type: 'call', due_date: '', due_time: '10:00', notes: '' })
    qc.invalidateQueries({ queryKey: ['reminders'] })
  }

  const statusColor: Record<string, string> = {
    pending: 'bg-amber-50 text-amber-700',
    overdue: 'bg-red-50 text-red-700',
    completed: 'bg-emerald-50 text-emerald-700',
    cancelled: 'bg-slate-100 text-slate-600',
  }

  const rows = filtered.map((r: Record<string, unknown>) => ({
    ...r,
    actions: r.id,
  }))

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('follow_ups')}</h1>
          <p className="text-sm text-slate-500">{t('follow_ups_subtitle')}</p>
        </div>
        <Button onClick={() => setOpen(true)}><Plus className="me-2 h-4 w-4" />{t('add_reminder')}</Button>
      </div>

      <div className="mb-4 flex gap-2">
        {(['all', 'today', 'overdue'] as const).map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={cn(
            'rounded-lg px-3 py-1.5 text-sm font-medium capitalize',
            filter === f ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
          )}>{t(`filter_${f}`)}</button>
        ))}
      </div>

      <SortableTable
        columns={[
          { key: 'title', label_en: 'Title', label_ar: 'العنوان' },
          { key: 'reminder_type', label_en: 'Type', label_ar: 'النوع' },
          { key: 'due_date', label_en: 'Date', label_ar: 'التاريخ' },
          { key: 'due_time', label_en: 'Time', label_ar: 'الوقت' },
          { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
          { key: 'notes', label_en: 'Notes', label_ar: 'ملاحظات' },
        ]}
        rows={rows.map((r: Record<string, unknown>) => ({
          ...r,
          reminder_type: String(r.reminder_type).replace('_', ' '),
        }))}
        loading={isLoading}
        onExport={() => exportRowsToExcel(reminders, 'reminders')}
      />

      <div className="mt-4 space-y-2">
        {filtered.slice(0, 5).map((r: Record<string, unknown>) => (
          <div key={r.id as number} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-3">
              <Phone className="h-5 w-5 text-primary-600" />
              <div>
                <p className="font-medium">{r.title as string}</p>
                <p className="text-xs text-slate-500">{r.due_date as string} {r.due_time as string}</p>
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

      <Modal open={open} onClose={() => setOpen(false)} title={t('add_reminder')}>
        <form onSubmit={createReminder} className="space-y-4">
          <Input label={t('title')} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <div>
            <label className="mb-1 block text-sm font-medium">{t('reminder_type')}</label>
            <select className="input-field" value={form.reminder_type} onChange={(e) => setForm({ ...form, reminder_type: e.target.value })}>
              <option value="call">{t('reminder_call')}</option>
              <option value="visit">{t('reminder_visit')}</option>
              <option value="meeting">{t('reminder_meeting')}</option>
              <option value="payment">{t('reminder_payment')}</option>
            </select>
          </div>
          <Input label={t('due_date')} type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} required />
          <Input label={t('due_time')} type="time" value={form.due_time} onChange={(e) => setForm({ ...form, due_time: e.target.value })} />
          <Input label={t('notes')} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <div className="flex gap-3"><Button type="submit">{t('save')}</Button><Button type="button" variant="secondary" onClick={() => setOpen(false)}>{t('cancel')}</Button></div>
        </form>
      </Modal>
    </div>
  )
}
