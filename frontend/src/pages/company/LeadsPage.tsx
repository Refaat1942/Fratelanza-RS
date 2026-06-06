import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Card } from '@/components/ui/Card'
import api from '@/lib/api'
import type { Lead, Paginated } from '@/types'

export function LeadsPage() {
  const { t } = useTranslation()
  const { data, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Lead>>('/leads')
      return data
    },
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('leads')}</h1>
      <Card>
        {isLoading ? (
          <p className="text-slate-500">{t('loading')}</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
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
                  <td className="py-3">{lead.id}</td>
                  <td className="py-3 font-medium">{lead.full_name}</td>
                  <td className="py-3">{lead.mobile}</td>
                  <td className="py-3">{lead.source}</td>
                  <td className="py-3">
                    <span className="rounded-full bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700">
                      {lead.stage}
                    </span>
                  </td>
                  <td className="py-3">{lead.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
