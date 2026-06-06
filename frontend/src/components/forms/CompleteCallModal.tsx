import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'

const OUTCOMES = [
  'answered_interested',
  'answered_callback',
  'no_answer',
  'not_interested',
] as const

const LEAD_STAGES = [
  'new',
  'contacted',
  'interested',
  'site_visit',
  'negotiation',
  'reservation',
  'contract_signed',
  'lost',
] as const

interface CompleteCallModalProps {
  open: boolean
  onClose: () => void
  reminderId?: number
  leadStage?: string
  onCompleted?: () => void
}

export function CompleteCallModal({
  open,
  onClose,
  reminderId,
  leadStage,
  onCompleted,
}: CompleteCallModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    outcome: 'answered_interested',
    outcome_notes: '',
    next_call_date: '',
    next_call_time: '10:00',
    new_lead_stage: '',
    schedule_next: true,
  })

  useEffect(() => {
    if (open) {
      const nextWeek = new Date()
      nextWeek.setDate(nextWeek.getDate() + 3)
      setForm({
        outcome: 'answered_interested',
        outcome_notes: '',
        next_call_date: nextWeek.toISOString().slice(0, 10),
        next_call_time: '10:00',
        new_lead_stage: leadStage || '',
        schedule_next: true,
      })
    }
  }, [open, leadStage])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reminderId) return
    setLoading(true)
    try {
      const scheduleNext = form.schedule_next && form.outcome !== 'not_interested'
      await api.post(`/reminders/${reminderId}/complete`, {
        outcome: form.outcome,
        outcome_notes: form.outcome_notes || undefined,
        next_call_date: scheduleNext ? form.next_call_date : undefined,
        next_call_time: scheduleNext ? form.next_call_time : undefined,
        new_lead_stage: form.new_lead_stage || undefined,
      })
      await qc.invalidateQueries({ queryKey: ['reminders'] })
      await qc.invalidateQueries({ queryKey: ['reminders-queue'] })
      await qc.invalidateQueries({ queryKey: ['reminders-history'] })
      await qc.invalidateQueries({ queryKey: ['reminders-summary'] })
      await qc.invalidateQueries({ queryKey: ['leads-kanban'] })
      onCompleted?.()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('complete_call')} className="max-w-lg">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">{t('call_outcome')}</label>
          <select
            className="input-field"
            value={form.outcome}
            onChange={(e) => setForm({ ...form, outcome: e.target.value })}
          >
            {OUTCOMES.map((o) => (
              <option key={o} value={o}>{t(`outcome_${o}`)}</option>
            ))}
          </select>
        </div>
        <Input
          label={t('call_notes')}
          value={form.outcome_notes}
          onChange={(e) => setForm({ ...form, outcome_notes: e.target.value })}
          placeholder={t('call_notes_placeholder')}
        />
        {form.outcome !== 'not_interested' && (
          <>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.schedule_next}
                onChange={(e) => setForm({ ...form, schedule_next: e.target.checked })}
              />
              {t('schedule_next_call')}
            </label>
            {form.schedule_next && (
              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label={t('next_call_date')}
                  type="date"
                  value={form.next_call_date}
                  onChange={(e) => setForm({ ...form, next_call_date: e.target.value })}
                />
                <Input
                  label={t('due_time')}
                  type="time"
                  value={form.next_call_time}
                  onChange={(e) => setForm({ ...form, next_call_time: e.target.value })}
                />
              </div>
            )}
          </>
        )}
        <div>
          <label className="mb-1 block text-sm font-medium">{t('update_lead_stage')}</label>
          <select
            className="input-field"
            value={form.new_lead_stage}
            onChange={(e) => setForm({ ...form, new_lead_stage: e.target.value })}
          >
            <option value="">{t('keep_current_stage')}</option>
            {LEAD_STAGES.map((s) => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>
        </div>
        <div className="flex gap-3">
          <Button type="submit" loading={loading}>{t('save_call_result')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
