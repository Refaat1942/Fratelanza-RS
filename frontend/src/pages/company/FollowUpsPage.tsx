import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Phone, Plus, MessageCircle, Calendar, CheckCircle, Clock } from 'lucide-react'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { ReminderFormModal } from '@/components/forms/ReminderFormModal'
import { CompleteCallModal } from '@/components/forms/CompleteCallModal'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { telLink, whatsappLink } from '@/lib/phone'
import { cn } from '@/lib/utils'

type ReminderRow = {
  id: number
  title: string
  linked_to: string
  mobile: string
  whatsapp: string
  due_date: string
  due_time: string
  status: string
  notes: string
  lead_stage: string
  call_outcome: string
  outcome_notes: string
  lead_id?: number
  customer_id?: number
}

type QueueResponse = {
  today_and_overdue: ReminderRow[]
  upcoming_week: ReminderRow[]
  counts: { overdue: number; due_today: number; upcoming: number }
}

export function FollowUpsPage() {
  const { t } = useTranslation()
  const { formatInteger, formatPhone, localizeDigits } = useFormatNumber()
  const qc = useQueryClient()
  const [tab, setTab] = useState<'queue' | 'history'>('queue')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [scheduleOpen, setScheduleOpen] = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)

  const { data: summary } = useQuery({
    queryKey: ['reminders-summary'],
    queryFn: async () => (await api.get('/reminders/summary')).data,
  })

  const { data: queue, isLoading: queueLoading } = useQuery({
    queryKey: ['reminders-queue'],
    queryFn: async () => (await api.get<QueueResponse>('/reminders/queue')).data,
  })

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['reminders-history'],
    queryFn: async () => (await api.get<ReminderRow[]>('/reminders/history')).data,
    enabled: tab === 'history',
  })

  const { data: detail } = useQuery({
    queryKey: ['reminder-detail', selectedId],
    queryFn: async () => (await api.get(`/reminders/${selectedId}`)).data,
    enabled: !!selectedId,
  })

  const queueItems = [
    ...(queue?.today_and_overdue ?? []),
    ...(queue?.upcoming_week ?? []),
  ]

  const list = tab === 'queue' ? queueItems : history
  const selected = list.find((r) => r.id === selectedId) ?? detail
  const isLoading = tab === 'queue' ? queueLoading : historyLoading

  const reschedule = useMutation({
    mutationFn: async ({ id, due_date }: { id: number; due_date: string }) => {
      await api.post(`/reminders/${id}/reschedule`, { due_date, due_time: '10:00' })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['reminders-queue'] })
      qc.invalidateQueries({ queryKey: ['reminders-summary'] })
    },
  })

  const statusColor: Record<string, string> = {
    pending: 'bg-amber-50 text-amber-700',
    overdue: 'bg-red-50 text-red-700',
    completed: 'bg-emerald-50 text-emerald-700',
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('call_queue')}</h1>
          <p className="text-sm text-slate-500">{t('call_queue_help')}</p>
        </div>
        <Button onClick={() => setScheduleOpen(true)}>
          <Plus className="me-2 h-4 w-4" />{t('schedule_call')}
        </Button>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">{t('overdue')}</p>
          <p className="text-2xl font-bold text-red-900">{formatInteger(queue?.counts?.overdue ?? summary?.overdue)}</p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-800">{t('calls_today')}</p>
          <p className="text-2xl font-bold text-amber-900">{formatInteger(queue?.counts?.due_today ?? summary?.today)}</p>
        </div>
        <div className="rounded-xl border border-primary-200 bg-primary-50 p-4">
          <p className="text-sm text-primary-800">{t('upcoming_week')}</p>
          <p className="text-2xl font-bold text-primary-900">{formatInteger(queue?.counts?.upcoming)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-600">{t('completed_calls')}</p>
          <p className="text-2xl font-bold text-slate-900">{formatInteger(history.length)}</p>
        </div>
      </div>

      <div className="mb-4 flex gap-2">
        {(['queue', 'history'] as const).map((f) => (
          <button
            key={f}
            onClick={() => { setTab(f); setSelectedId(null) }}
            className={cn(
              'rounded-lg px-3 py-1.5 text-sm font-medium capitalize',
              tab === f ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
            )}
          >
            {t(f === 'queue' ? 'call_queue_tab' : 'call_history_tab')}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2 space-y-2">
          {!isLoading && list.length === 0 ? (
            <EmptyState
              icon={<Phone className="h-10 w-10" />}
              title={tab === 'queue' ? t('no_calls_in_queue') : t('no_call_history')}
              description={t('no_reminders_help')}
              actionLabel={t('schedule_call')}
              onAction={() => setScheduleOpen(true)}
            />
          ) : (
            list.map((r) => (
              <button
                key={r.id}
                onClick={() => setSelectedId(r.id)}
                className={cn(
                  'w-full rounded-xl border p-4 text-start transition',
                  selectedId === r.id ? 'border-primary-400 bg-primary-50' : 'border-slate-200 bg-white hover:border-primary-200',
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-900">{r.linked_to || r.title}</p>
                    <p className="text-xs text-slate-500">{r.title}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      <Clock className="me-1 inline h-3 w-3" />
                      {localizeDigits(`${r.due_date} ${r.due_time}`)}
                    </p>
                  </div>
                  <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', statusColor[r.status] ?? 'bg-slate-100')}>
                    {tab === 'history' && r.call_outcome ? t(`outcome_${r.call_outcome}`) : r.status}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="lg:col-span-3 rounded-xl border border-slate-200 bg-white p-6">
          {!selected ? (
            <p className="text-sm text-slate-500">{t('select_call_to_work')}</p>
          ) : (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl font-bold text-slate-900">{selected.linked_to || selected.title}</h2>
                <p className="text-sm text-slate-500">{selected.title}</p>
                {selected.lead_stage && (
                  <span className="mt-2 inline-block rounded-full bg-violet-50 px-2 py-0.5 text-xs text-violet-700">
                    {t('lead_stage')}: {selected.lead_stage.replace('_', ' ')}
                  </span>
                )}
              </div>

              {selected.mobile && tab === 'queue' && (
                <div className="flex flex-wrap gap-2">
                  <a href={telLink(selected.mobile)} className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">
                    <Phone className="h-4 w-4" />{t('call_now')} {formatPhone(selected.mobile)}
                  </a>
                  <a
                    href={whatsappLink(selected.whatsapp || selected.mobile)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                  >
                    <MessageCircle className="h-4 w-4" />WhatsApp
                  </a>
                </div>
              )}

              {selected.notes && (
                <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                  <p className="mb-1 font-medium text-slate-900">{t('notes')}</p>
                  {selected.notes}
                </div>
              )}

              {tab === 'history' && selected.outcome_notes && (
                <div className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-900">
                  <p className="mb-1 font-medium">{t('call_notes')}</p>
                  {selected.outcome_notes}
                </div>
              )}

              {detail?.activity_timeline?.length > 0 && (
                <div>
                  <p className="mb-2 font-medium text-slate-900">{t('customer_timeline')}</p>
                  <ul className="space-y-2 text-sm">
                    {detail.activity_timeline.map((a: { title: string; description: string; date: string }, i: number) => (
                      <li key={i} className="rounded-lg border border-slate-100 px-3 py-2">
                        <p className="font-medium">{a.title}</p>
                        {a.description && <p className="text-slate-500">{a.description}</p>}
                        <p className="text-xs text-slate-400">{a.date}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {tab === 'queue' && selected.status !== 'completed' && (
                <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-4">
                  <Button onClick={() => setCompleteOpen(true)}>
                    <CheckCircle className="me-2 h-4 w-4" />{t('complete_call')}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      const tomorrow = new Date()
                      tomorrow.setDate(tomorrow.getDate() + 1)
                      reschedule.mutate({ id: selected.id, due_date: tomorrow.toISOString().slice(0, 10) })
                    }}
                  >
                    <Calendar className="me-2 h-4 w-4" />{t('reschedule_tomorrow')}
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <ReminderFormModal
        open={scheduleOpen}
        onClose={() => {
          setScheduleOpen(false)
          qc.invalidateQueries({ queryKey: ['reminders-queue'] })
          qc.invalidateQueries({ queryKey: ['reminders-summary'] })
        }}
      />
      <CompleteCallModal
        open={completeOpen}
        reminderId={selected?.id}
        leadStage={selected?.lead_stage}
        onClose={() => setCompleteOpen(false)}
        onCompleted={() => {
          setSelectedId(null)
          qc.invalidateQueries({ queryKey: ['reminders-queue'] })
          qc.invalidateQueries({ queryKey: ['reminders-history'] })
        }}
      />
    </div>
  )
}
