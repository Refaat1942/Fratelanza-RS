import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Phone, Search, Upload, UserPlus } from 'lucide-react'
import { ReminderFormModal } from '@/components/forms/ReminderFormModal'
import { CustomerImportModal } from '@/components/forms/CustomerImportModal'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ClientFormModal } from '@/components/forms/ClientFormModal'
import api from '@/lib/api'
import type { Customer, Paginated } from '@/types'

export function CustomersPage() {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [reminderOpen, setReminderOpen] = useState(false)
  const [reminderCustomer, setReminderCustomer] = useState<{ id: number; name: string } | null>(null)
  const [search, setSearch] = useState('')
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Customer>>('/customers')
      return data
    },
  })

  const filtered = useMemo(() => {
    if (!data?.items || !search) return data?.items ?? []
    const q = search.toLowerCase()
    return data.items.filter((c) =>
      [c.full_name_ar, c.full_name_en, c.mobile, c.email].some((v) => v?.toLowerCase().includes(q)),
    )
  }, [data, search])

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t('customers')}</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setImportOpen(true)}>
            <Upload className="me-2 h-4 w-4" />
            {t('bulk_import')}
          </Button>
          <Button onClick={() => setOpen(true)}>
            <UserPlus className="me-2 h-4 w-4" />
            {t('add_client')}
          </Button>
        </div>
      </div>
      <Card>
        <div className="relative mb-4 max-w-md">
          <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('search_table')}
            className="input-field ps-10"
          />
        </div>
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
                <th className="pb-3 text-start">{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3">{c.id}</td>
                  <td className="py-3 font-medium">
                    {i18n.language === 'ar' ? c.full_name_ar : c.full_name_en}
                  </td>
                  <td className="py-3">{c.mobile}</td>
                  <td className="py-3 text-slate-500">{c.email || '-'}</td>
                  <td className="py-3 text-slate-500">{(c as Customer & { city?: string }).city || '-'}</td>
                  <td className="py-3">
                    <button
                      onClick={() => {
                        setReminderCustomer({ id: c.id, name: i18n.language === 'ar' ? c.full_name_ar : c.full_name_en })
                        setReminderOpen(true)
                      }}
                      className="inline-flex items-center gap-1 text-xs font-medium text-primary-700 hover:underline"
                    >
                      <Phone className="h-3.5 w-3.5" />{t('schedule_call')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
      <ClientFormModal open={open} onClose={() => { setOpen(false); refetch() }} />
      <CustomerImportModal open={importOpen} onClose={() => { setImportOpen(false); refetch() }} />
      <ReminderFormModal
        open={reminderOpen}
        onClose={() => { setReminderOpen(false); setReminderCustomer(null) }}
        customerId={reminderCustomer?.id}
        defaultTitle={reminderCustomer ? `${t('schedule_call')}: ${reminderCustomer.name}` : ''}
      />
    </div>
  )
}
