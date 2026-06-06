import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Phone, Calendar, Pencil, Trash2, ChevronLeft, ChevronRight, Target } from 'lucide-react'
import { ReminderFormModal } from '@/components/forms/ReminderFormModal'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import api from '@/lib/api'
import { telLink } from '@/lib/phone'
import { cn } from '@/lib/utils'

const STAGES = [
  { key: 'new', accent: 'border-slate-400', header: 'bg-slate-100 text-slate-800', dot: 'bg-slate-400' },
  { key: 'contacted', accent: 'border-blue-400', header: 'bg-blue-50 text-blue-900', dot: 'bg-blue-500' },
  { key: 'interested', accent: 'border-cyan-400', header: 'bg-cyan-50 text-cyan-900', dot: 'bg-cyan-500' },
  { key: 'site_visit', accent: 'border-violet-400', header: 'bg-violet-50 text-violet-900', dot: 'bg-violet-500' },
  { key: 'negotiation', accent: 'border-amber-400', header: 'bg-amber-50 text-amber-900', dot: 'bg-amber-500' },
  { key: 'reservation', accent: 'border-orange-400', header: 'bg-orange-50 text-orange-900', dot: 'bg-orange-500' },
  { key: 'contract_signed', accent: 'border-emerald-400', header: 'bg-emerald-50 text-emerald-900', dot: 'bg-emerald-500' },
  { key: 'lost', accent: 'border-red-300', header: 'bg-red-50 text-red-800', dot: 'bg-red-400' },
] as const

interface LeadCard {
  id: number
  full_name: string
  mobile: string
  source: string
  score: number
  ai_qualification?: string
  next_follow_up?: string
}

interface LeadKanbanProps {
  onEdit?: (lead: LeadCard) => void
}

export function LeadKanban({ onEdit }: LeadKanbanProps) {
  const { t } = useTranslation()
  const { formatInteger, formatPhone, localizeDigits } = useFormatNumber()
  const qc = useQueryClient()
  const [scheduleLead, setScheduleLead] = useState<LeadCard | null>(null)
  const deleteLead = useDeleteEntity('/leads', ['leads', 'leads-kanban'])

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
    },
  })

  const totalLeads = STAGES.reduce((sum, s) => sum + (data?.[s.key]?.length ?? 0), 0)

  const stageLabel = (key: string) => t(`lead_stage_${key}`, key.replace(/_/g, ' '))

  const moveStage = (leadId: number, currentKey: string, dir: -1 | 1) => {
    const idx = STAGES.findIndex((s) => s.key === currentKey)
    const next = STAGES[idx + dir]
    if (next) moveLead.mutate({ id: leadId, stage: next.key })
  }

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center text-slate-500">{t('loading')}</div>
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary-600" />
          <span className="font-semibold text-slate-900">{t('sales_pipeline')}</span>
        </div>
        <span className="text-sm text-slate-500">{formatInteger(totalLeads)} {t('leads')}</span>
        <div className="ms-auto flex flex-wrap gap-2">
          {STAGES.slice(0, 5).map((s) => (
            <span key={s.key} className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium', s.header)}>
              <span className={cn('h-1.5 w-1.5 rounded-full', s.dot)} />
              {formatInteger(data?.[s.key]?.length ?? 0)}
            </span>
          ))}
        </div>
      </div>

      <div className="kanban-scroll flex gap-3 overflow-x-auto pb-4">
        {STAGES.map(({ key, accent, header, dot }) => (
          <div
            key={key}
            className={cn(
              'flex w-[280px] flex-shrink-0 flex-col rounded-xl border bg-slate-50/80 shadow-sm',
              accent.replace('border-', 'border-t-4 border-t-'),
            )}
          >
            <div className={cn('flex items-center justify-between rounded-t-lg px-3 py-2.5', header)}>
              <div className="flex items-center gap-2">
                <span className={cn('h-2 w-2 rounded-full', dot)} />
                <span className="text-sm font-semibold">{stageLabel(key)}</span>
              </div>
              <span className="rounded-full bg-white/80 px-2 py-0.5 text-xs font-bold shadow-sm">
                {formatInteger(data?.[key]?.length ?? 0)}
              </span>
            </div>

            <div className="flex min-h-[320px] flex-1 flex-col gap-2 p-2">
              {(data?.[key] ?? []).length === 0 ? (
                <p className="py-8 text-center text-xs text-slate-400">{t('no_leads_in_stage')}</p>
              ) : (
                (data?.[key] ?? []).map((lead) => (
                  <div
                    key={lead.id}
                    className="group rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition hover:border-primary-200 hover:shadow-md"
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <p className="font-semibold leading-tight text-slate-900">{lead.full_name}</p>
                      <span className="shrink-0 rounded-md bg-primary-100 px-1.5 py-0.5 text-xs font-bold text-primary-800">
                        {formatInteger(lead.score)}
                      </span>
                    </div>
                    <a href={telLink(lead.mobile)} className="text-xs font-medium text-primary-600 hover:underline">
                      {formatPhone(lead.mobile)}
                    </a>
                    {lead.next_follow_up && (
                      <p className="mt-1.5 flex items-center gap-1 text-xs text-amber-700">
                        <Calendar className="h-3 w-3 shrink-0" />
                        {localizeDigits(lead.next_follow_up)}
                      </p>
                    )}
                    <p className="mt-2 text-xs capitalize text-slate-400">{lead.source.replace('_', ' ')}</p>

                    <div className="mt-3 flex items-center gap-1 border-t border-slate-100 pt-2">
                      <button
                        type="button"
                        onClick={() => moveStage(lead.id, key, -1)}
                        disabled={key === STAGES[0].key}
                        className="rounded p-1 text-slate-400 hover:bg-slate-100 disabled:opacity-30"
                        title={t('move_back')}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => moveStage(lead.id, key, 1)}
                        disabled={key === STAGES[STAGES.length - 1].key}
                        className="rounded p-1 text-slate-400 hover:bg-slate-100 disabled:opacity-30"
                        title={t('move_forward')}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setScheduleLead(lead)}
                        className="ms-auto flex items-center gap-1 rounded-md bg-primary-50 px-2 py-1 text-xs text-primary-700 hover:bg-primary-100"
                      >
                        <Phone className="h-3 w-3" />
                      </button>
                      {onEdit && (
                        <button type="button" onClick={() => onEdit(lead)} className="rounded p-1 text-slate-500 hover:bg-slate-100" title={t('edit')}>
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => confirmDelete(t) && deleteLead.mutate(lead.id)}
                        className="rounded p-1 text-red-500 hover:bg-red-50"
                        title={t('delete')}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
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
        }}
      />
    </>
  )
}
