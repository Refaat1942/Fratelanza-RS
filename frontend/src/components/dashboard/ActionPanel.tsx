import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Phone, AlertTriangle, Users, Wallet, ChevronRight } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { formatEGP } from '@/lib/currency'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

export function ActionPanel() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const { data: reminderSummary } = useQuery({
    queryKey: ['reminders-summary'],
    queryFn: async () => (await api.get('/reminders/summary')).data,
  })

  const { data: todayReminders = [] } = useQuery({
    queryKey: ['reminders-today'],
    queryFn: async () => (await api.get('/reminders', { params: { due_today: true } })).data,
  })

  const { data: dashboard } = useQuery({
    queryKey: ['company-dashboard'],
    queryFn: async () => (await api.get('/dashboard/company')).data,
  })

  const { data: employees = [] } = useQuery({
    queryKey: ['hr-employees-count'],
    queryFn: async () => (await api.get('/hr/employees')).data,
  })

  const overdue = dashboard?.stats?.overdue_amount ?? 0

  const items = [
    {
      icon: Phone,
      color: 'text-primary-600 bg-primary-50',
      title: t('follow_ups_today'),
      value: String(reminderSummary?.today ?? 0),
      desc: reminderSummary?.overdue ? `${reminderSummary.overdue} ${t('overdue')}` : t('no_overdue_calls'),
      onClick: () => navigate('/follow-ups'),
    },
    {
      icon: AlertTriangle,
      color: 'text-red-600 bg-red-50',
      title: t('overdue_amount'),
      value: formatEGP(overdue),
      desc: t('view_collections'),
      onClick: () => navigate('/collections'),
    },
    {
      icon: Users,
      color: 'text-violet-600 bg-violet-50',
      title: t('employees'),
      value: String(employees.length),
      desc: t('manage_hr'),
      onClick: () => navigate('/hr'),
    },
    {
      icon: Wallet,
      color: 'text-emerald-600 bg-emerald-50',
      title: t('finance'),
      value: t('view_reports'),
      desc: t('finance_quick_desc'),
      onClick: () => navigate('/finance'),
    },
  ]

  return (
    <div className="mt-6 grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <Card>
          <h3 className="mb-4 font-semibold text-slate-900">{t('action_center')}</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {items.map((item) => (
              <button
                key={item.title}
                onClick={item.onClick}
                className="flex items-center gap-4 rounded-xl border border-slate-200 p-4 text-start transition hover:border-primary-200 hover:bg-primary-50/50"
              >
                <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg', item.color)}>
                  <item.icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-slate-500">{item.title}</p>
                  <p className="text-lg font-bold text-slate-900">{item.value}</p>
                  <p className="text-xs text-slate-400">{item.desc}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </button>
            ))}
          </div>
        </Card>
      </div>
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">{t('calls_today')}</h3>
          <button onClick={() => navigate('/follow-ups')} className="text-xs font-medium text-primary-700 hover:underline">
            {t('view_all')}
          </button>
        </div>
        {todayReminders.length === 0 ? (
          <p className="text-sm text-slate-500">{t('no_calls_today')}</p>
        ) : (
          <ul className="space-y-2">
            {todayReminders.slice(0, 5).map((r: { id: number; title: string; due_time: string; linked_to?: string }) => (
              <li key={r.id} className="rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <p className="font-medium text-slate-800">{r.title}</p>
                <p className="text-xs text-slate-500">{r.due_time}{r.linked_to ? ` · ${r.linked_to}` : ''}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
