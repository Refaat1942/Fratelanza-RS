import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'

interface ReminderFormModalProps {
  open: boolean
  onClose: () => void
  customerId?: number
  leadId?: number
  defaultTitle?: string
}

export function ReminderFormModal({ open, onClose, customerId, leadId, defaultTitle }: ReminderFormModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    title: '',
    reminder_type: 'call',
    due_date: new Date().toISOString().slice(0, 10),
    due_time: '10:00',
    notes: '',
    customer_id: '' as string | number,
    lead_id: '' as string | number,
  })

  const { data: customers } = useQuery({
    queryKey: ['customers-picker'],
    queryFn: async () => (await api.get('/customers', { params: { page_size: 100 } })).data.items,
    enabled: open,
  })

  const { data: leads } = useQuery({
    queryKey: ['leads-picker'],
    queryFn: async () => (await api.get('/leads', { params: { page_size: 100 } })).data.items,
    enabled: open,
  })

  useEffect(() => {
    if (open) {
      setForm((f) => ({
        ...f,
        title: defaultTitle || f.title,
        customer_id: customerId ?? '',
        lead_id: leadId ?? '',
        due_date: new Date().toISOString().slice(0, 10),
      }))
    }
  }, [open, customerId, leadId, defaultTitle])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/reminders', {
        title: form.title,
        reminder_type: form.reminder_type,
        due_date: form.due_date,
        due_time: form.due_time,
        notes: form.notes,
        customer_id: form.customer_id ? Number(form.customer_id) : undefined,
        lead_id: form.lead_id ? Number(form.lead_id) : undefined,
      })
      qc.invalidateQueries({ queryKey: ['reminders'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('add_reminder')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('title')} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required placeholder={t('reminder_title_placeholder')} />
        <div>
          <label className="mb-1 block text-sm font-medium">{t('customers')}</label>
          <select className="input-field" value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}>
            <option value="">{t('optional')}</option>
            {customers?.map((c: { id: number; full_name_en: string; mobile: string }) => (
              <option key={c.id} value={c.id}>{c.full_name_en} — {c.mobile}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">{t('leads')}</label>
          <select className="input-field" value={form.lead_id} onChange={(e) => setForm({ ...form, lead_id: e.target.value })}>
            <option value="">{t('optional')}</option>
            {leads?.map((l: { id: number; full_name: string; mobile: string }) => (
              <option key={l.id} value={l.id}>{l.full_name} — {l.mobile}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">{t('reminder_type')}</label>
          <select className="input-field" value={form.reminder_type} onChange={(e) => setForm({ ...form, reminder_type: e.target.value })}>
            <option value="call">{t('reminder_call')}</option>
            <option value="visit">{t('reminder_visit')}</option>
            <option value="meeting">{t('reminder_meeting')}</option>
            <option value="payment">{t('reminder_payment')}</option>
          </select>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label={t('due_date')} type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} required />
          <Input label={t('due_time')} type="time" value={form.due_time} onChange={(e) => setForm({ ...form, due_time: e.target.value })} />
        </div>
        <Input label={t('notes')} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <div className="flex gap-3">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
