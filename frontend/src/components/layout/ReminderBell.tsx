import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Bell } from 'lucide-react'
import api from '@/lib/api'

export function ReminderBell() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const { data: summary } = useQuery({
    queryKey: ['reminders-summary'],
    queryFn: async () => (await api.get('/reminders/summary')).data,
    refetchInterval: 60000,
  })

  const { data: queue } = useQuery({
    queryKey: ['reminders-queue'],
    queryFn: async () => (await api.get('/reminders/queue')).data,
    enabled: open,
  })
  const today = queue?.today_and_overdue ?? []

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const count = (summary?.today ?? 0) + (summary?.overdue ?? 0)

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100">
        <Bell className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute end-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute end-0 top-full z-50 mt-1 w-72 rounded-xl border border-slate-200 bg-white shadow-lg">
          <div className="border-b border-slate-100 px-4 py-3">
            <p className="font-semibold text-slate-900">{t('calls_today')}</p>
            <p className="text-xs text-slate-500">{summary?.overdue ?? 0} {t('overdue')}</p>
          </div>
          {today.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">{t('no_calls_today')}</p>
          ) : (
            <ul className="max-h-60 overflow-y-auto py-2">
              {today.map((r: { id: number; title: string; due_time: string; linked_to?: string; status?: string }) => (
                <li key={r.id}>
                  <button
                    onClick={() => { navigate('/follow-ups'); setOpen(false) }}
                    className="w-full px-4 py-2 text-start text-sm hover:bg-slate-50"
                  >
                    <p className="font-medium">{r.linked_to || r.title}</p>
                    <p className="text-xs text-slate-500">
                      {r.due_time}{r.status === 'overdue' ? ` · ${t('overdue')}` : ''}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <button onClick={() => { navigate('/follow-ups'); setOpen(false) }} className="w-full border-t border-slate-100 px-4 py-2 text-sm font-medium text-primary-700 hover:bg-slate-50">
            {t('view_all_reminders')}
          </button>
        </div>
      )}
    </div>
  )
}
