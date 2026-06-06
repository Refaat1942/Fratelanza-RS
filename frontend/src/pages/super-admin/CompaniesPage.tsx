import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Card } from '@/components/ui/Card'
import api from '@/lib/api'
import type { Company, Paginated } from '@/types'

export function CompaniesPage() {
  const { t, i18n } = useTranslation()
  const { data, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Company>>('/super-admin/companies')
      return data
    },
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('companies')}</h1>
      <Card>
        {isLoading ? (
          <p className="text-slate-500">{t('loading')}</p>
        ) : data?.items.length === 0 ? (
          <p className="text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-3 text-start font-medium">#</th>
                  <th className="pb-3 text-start font-medium">{t('companies')}</th>
                  <th className="pb-3 text-start font-medium">{t('status')}</th>
                  <th className="pb-3 text-start font-medium">Code</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((company) => (
                  <tr key={company.id} className="border-b border-slate-100">
                    <td className="py-3">{company.id}</td>
                    <td className="py-3 font-medium">
                      {i18n.language === 'ar' ? company.name_ar : company.name_en}
                    </td>
                    <td className="py-3">
                      <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                        {company.status}
                      </span>
                    </td>
                    <td className="py-3 text-slate-500">{company.code}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
