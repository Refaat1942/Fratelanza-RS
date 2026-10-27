import { useState, useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Bell, Phone, CheckCheck } from 'lucide-react'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { usePermissionsStore } from '@/stores/permissionsStore'

type Alert = {
  id: number; title_ar: string; title_en: string; message_ar: string | null; message_en: string | null
  is_read: boolean; reference_type: string | null; created_at: string
}

/** Where an alert leads (rent due/overdue, lease expiry, owner settlement due). */
const ALERT_ROUTES: Record<string, string> = {
  rent_receivable: '/rentals?tab=receivables',
  rental_contract: '/rentals',
  property_owner: '/owners?tab=upcoming',
}

export function ReminderBell() {
  const { t, i18n } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const canFollowUps = usePermissionsStore((s) => s.can('follow_ups'))
  const ar = i18n.language === 'ar'

  const { data: alerts = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => (await api.get<Alert[]>('/notifications')).data,
    refetchInterval: 60000,
  })
  const { data: summary } = useQuery({
    queryKey: ['reminders-summary'],
    queryFn: async () => (await api.get('/reminders/summary')).data,
    refetchInterval: 60000,
    enabled: canFollowUps,
  })
  const { data: queue } = useQuery({
    queryKey: ['reminders-queue'],
    queryFn: async () => (await api.get('/reminders/queue')).data,
    enabled: open && canFollowUps,
  })
  const calls = queue?.today_and_overdue ?? []

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const unread = alerts.filter((a) => !a.is_read).length
  const callCount = canFollowUps ? (summary?.today ?? 0) + (summary?.overdue ?? 0) : 0
  const count = unread + callCount

  const openAlert = async (a: Alert) => {
    if (!a.is_read) {
      await api.post(`/notifications/${a.id}/read`).catch(() => {})
      qc.invalidateQueries({ queryKey: ['notifications'] })
    }
    setOpen(false)
    navigate(ALERT_ROUTES[a.reference_type ?? ''] ?? '/dashboard')
  }
  const readAll = async () => {
    await api.post('/notifications/read-all').catch(() => {})
    qc.invalidateQueries({ queryKey: ['notifications'] })
  }

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100" aria-label={t('re.alerts.title')}>
        <Bell className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute end-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {formatInteger(count)}
          </span>
        )}
      </button>
      {open && (
        <div className="fixed inset-x-3 top-16 z-50 rounded-xl sm:absolute sm:inset-x-auto sm:end-0 sm:top-full sm:mt-1 sm:w-80 border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <p className="font-semibold text-slate-900">{t('re.alerts.title')}</p>
            {unread > 0 && (
              <button onClick={readAll} className="inline-flex items-center gap-1 text-xs text-primary-700 hover:underline">
                <CheckCheck className="h-3.5 w-3.5" />{t('re.alerts.read_all')}
              </button>
            )}
          </div>
          <div className="max-h-[60vh] overflow-y-auto">
            {alerts.length === 0 && calls.length === 0 ? (
              <p className="p-4 text-sm text-slate-500">{t('re.alerts.none')}</p>
            ) : (
              <ul className="py-1">
                {alerts.slice(0, 20).map((a) => (
                  <li key={a.id}>
                    <button onClick={() => openAlert(a)} className={`w-full px-4 py-2 text-start text-sm hover:bg-slate-50 ${a.is_read ? 'opacity-60' : ''}`}>
                      <p className="flex items-center gap-2 font-medium">
                        {!a.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-red-500" />}
                        {ar ? a.title_ar : a.title_en}
                      </p>
                      <p className="text-xs text-slate-500">{ar ? a.message_ar : (a.message_en ?? a.message_ar)}</p>
                    </button>
                  </li>
                ))}
                {calls.map((r: { id: number; title: string; due_time: string; linked_to?: string; status?: string }) => (
                  <li key={`call-${r.id}`}>
                    <button onClick={() => { navigate('/follow-ups'); setOpen(false) }} className="w-full px-4 py-2 text-start text-sm hover:bg-slate-50">
                      <p className="flex items-center gap-2 font-medium"><Phone className="h-3.5 w-3.5 text-slate-400" />{r.linked_to || r.title}</p>
                      <p className="text-xs text-slate-500">{r.due_time}{r.status === 'overdue' ? ` · ${t('overdue')}` : ''}</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {canFollowUps && (
            <button onClick={() => { navigate('/follow-ups'); setOpen(false) }} className="w-full border-t border-slate-100 px-4 py-2 text-sm font-medium text-primary-700 hover:bg-slate-50">
              {t('view_all_reminders')}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
