import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { UserPlus } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ClientFormModal } from '@/components/forms/ClientFormModal'
import api from '@/lib/api'
import type { Customer, Paginated } from '@/types'

export function CustomersPage() {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Customer>>('/customers')
      return data
    },
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t('customers')}</h1>
        <Button onClick={() => setOpen(true)}>
          <UserPlus className="me-2 h-4 w-4" />
          {t('add_client')}
        </Button>
      </div>
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
                <th className="pb-3 text-start">{t('city')}</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((c) => (
                <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3">{c.id}</td>
                  <td className="py-3 font-medium">
                    {i18n.language === 'ar' ? c.full_name_ar : c.full_name_en}
                  </td>
                  <td className="py-3">{c.mobile}</td>
                  <td className="py-3 text-slate-500">{c.email || '-'}</td>
                  <td className="py-3 text-slate-500">{(c as Customer & { city?: string }).city || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
      <ClientFormModal open={open} onClose={() => { setOpen(false); refetch() }} />
    </div>
  )
}
