import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Phone, Calendar } from 'lucide-react'
import { ReminderFormModal } from '@/components/forms/ReminderFormModal'
import api from '@/lib/api'
import { telLink } from '@/lib/phone'
import { cn } from '@/lib/utils'

const STAGES = [
  { key: 'new', color: 'border-slate-300 bg-slate-50' },
  { key: 'contacted', color: 'border-blue-300 bg-blue-50' },
  { key: 'interested', color: 'border-cyan-300 bg-cyan-50' },
  { key: 'site_visit', color: 'border-violet-300 bg-violet-50' },
  { key: 'negotiation', color: 'border-amber-300 bg-amber-50' },
  { key: 'reservation', color: 'border-orange-300 bg-orange-50' },
  { key: 'contract_signed', color: 'border-emerald-300 bg-emerald-50' },
  { key: 'lost', color: 'border-red-300 bg-red-50' },
]

interface LeadCard {
  id: number
  full_name: string
  mobile: string
  source: string
  score: number
  ai_qualification?: string
  next_follow_up?: string
  pending_call_id?: number
  pending_call_date?: string
}

export function LeadKanban() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [scheduleLead, setScheduleLead] = useState<LeadCard | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['leads-kanban'],
    queryFn: async () => {
      const { data } = await api.get<Record<string, LeadCard[]>>('/leads/kanban')
      return data
    },
  })

  const moveLead = useMutation({
    mutationFn: async ({ id, stage }: { id: number; stage: string }) => {
      await api.patch(`/leads/${id}/stage?stage=${stage}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['leads-kanban'] })
      qc.invalidateQueries({ queryKey: ['reminders-queue'] })
      qc.invalidateQueries({ queryKey: ['reminders-summary'] })
    },
  })

  if (isLoading) return <p className="text-slate-500">{t('loading')}</p>

  return (
    <>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {STAGES.map(({ key, color }) => (
          <div key={key} className={cn('min-w-[240px] flex-shrink-0 rounded-xl border-2 p-3', color)}>
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-semibold capitalize">{key.replace('_', ' ')}</span>
              <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium">
                {data?.[key]?.length ?? 0}
              </span>
            </div>
            <div className="space-y-2">
              {(data?.[key] ?? []).map((lead) => (
                <div key={lead.id} className="rounded-lg bg-white p-3 shadow-sm">
                  <p className="font-medium text-slate-900">{lead.full_name}</p>
                  <a href={telLink(lead.mobile)} className="text-xs text-primary-600 hover:underline">
                    {lead.mobile}
                  </a>
                  {lead.next_follow_up && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-amber-700">
                      <Calendar className="h-3 w-3" />
                      {t('next_call')}: {lead.next_follow_up}
                    </p>
                  )}
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-slate-400">{lead.source}</span>
                    <span className="rounded bg-primary-100 px-1.5 py-0.5 text-xs font-medium text-primary-700">
                      {lead.score}
                    </span>
                  </div>
                  <div className="mt-2 flex gap-1">
                    <button
                      type="button"
                      onClick={() => setScheduleLead(lead)}
                      className="flex flex-1 items-center justify-center gap-1 rounded border border-primary-200 bg-primary-50 px-2 py-1 text-xs text-primary-700 hover:bg-primary-100"
                    >
                      <Phone className="h-3 w-3" />{t('schedule_call')}
                    </button>
                  </div>
                  <select
                    className="mt-2 w-full rounded border border-slate-200 text-xs"
                    value={key}
                    onChange={(e) => moveLead.mutate({ id: lead.id, stage: e.target.value })}
                  >
                    {STAGES.map((s) => (
                      <option key={s.key} value={s.key}>{s.key.replace('_', ' ')}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <ReminderFormModal
        open={!!scheduleLead}
        leadId={scheduleLead?.id}
        defaultTitle={scheduleLead ? `${t('schedule_call')}: ${scheduleLead.full_name}` : ''}
        onClose={() => {
          setScheduleLead(null)
          qc.invalidateQueries({ queryKey: ['leads-kanban'] })
          qc.invalidateQueries({ queryKey: ['reminders-queue'] })
        }}
      />
    </>
  )
}
