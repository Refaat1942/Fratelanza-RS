import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Card } from '@/components/ui/Card'
import api from '@/lib/api'
import type { Customer, Paginated } from '@/types'

export function CustomersPage() {
  const { t, i18n } = useTranslation()
  const { data, isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Customer>>('/customers')
      return data
    },
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('customers')}</h1>
      <Card>
        {isLoading ? (
          <p className="text-slate-500">{t('loading')}</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="pb-3 text-start">#</th>
                <th className="pb-3 text-start">{t('customers')}</th>
                <th className="pb-3 text-start">Mobile</th>
                <th className="pb-3 text-start">{t('email')}</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((c) => (
                <tr key={c.id} className="border-b border-slate-100">
                  <td className="py-3">{c.id}</td>
                  <td className="py-3 font-medium">
                    {i18n.language === 'ar' ? c.full_name_ar : c.full_name_en}
                  </td>
                  <td className="py-3">{c.mobile}</td>
                  <td className="py-3 text-slate-500">{c.email || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
