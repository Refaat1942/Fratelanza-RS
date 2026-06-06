import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { LayoutGrid, List } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { LeadKanban } from '@/components/crm/LeadKanban'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import type { Lead, Paginated } from '@/types'
import { cn } from '@/lib/utils'

export function LeadsPage() {
  const { t } = useTranslation()
  const { formatInteger, formatPhone } = useFormatNumber()
  const [view, setView] = useState<'kanban' | 'list'>('kanban')
  const { data, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Lead>>('/leads')
      return data
    },
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t('leads')}</h1>
        <div className="flex rounded-lg border border-slate-200 bg-white p-1">
          <button
            onClick={() => setView('kanban')}
            className={cn('flex items-center gap-1 rounded px-3 py-1.5 text-sm', view === 'kanban' && 'bg-primary-100 text-primary-700')}
          >
            <LayoutGrid className="h-4 w-4" /> {t('kanban_view')}
          </button>
          <button
            onClick={() => setView('list')}
            className={cn('flex items-center gap-1 rounded px-3 py-1.5 text-sm', view === 'list' && 'bg-primary-100 text-primary-700')}
          >
            <List className="h-4 w-4" /> {t('list_view')}
          </button>
        </div>
      </div>
      {view === 'kanban' ? (
        <LeadKanban />
      ) : (
        <Card>
          {isLoading ? (
            <p className="text-slate-500">{t('loading')}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head-gradient">
                  <th className="pb-3 text-start">#</th>
                  <th className="pb-3 text-start">Name</th>
                  <th className="pb-3 text-start">Mobile</th>
                  <th className="pb-3 text-start">Source</th>
                  <th className="pb-3 text-start">{t('status')}</th>
                  <th className="pb-3 text-start">Score</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((lead) => (
                  <tr key={lead.id} className="border-b border-slate-100">
                    <td className="py-3">{formatInteger(lead.id)}</td>
                    <td className="py-3 font-medium">{lead.full_name}</td>
                    <td className="py-3">{formatPhone(lead.mobile)}</td>
                    <td className="py-3">{lead.source}</td>
                    <td className="py-3">
                      <span className="rounded-full bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700">
                        {lead.stage}
                      </span>
                    </td>
                    <td className="py-3">{formatInteger(lead.score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}
    </div>
  )
}
