import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Building2, SlidersHorizontal, Pencil, CreditCard, Bell } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingState } from '@/components/ui/LoadingState'
import { Button } from '@/components/ui/Button'
import { CompanyFormModal } from '@/components/forms/CompanyFormModal'
import { CompanyEditModal } from '@/components/forms/CompanyEditModal'
import { CompanyModulesModal } from '@/components/forms/CompanyModulesModal'
import { CompanyBillingModal } from '@/components/forms/CompanyBillingModal'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import type { CompanyWithBilling, Paginated } from '@/types'

function PaymentStatusBadge({ status, t }: { status: string; t: (k: string) => string }) {
  const cls: Record<string, string> = {
    paid: 'status-paid', pending: 'status-pending', overdue: 'status-overdue', trial: 'status-pending',
  }
  return <span className={cls[status] || 'status-badge bg-slate-50 text-slate-600 ring-slate-500/20'}>{t(status)}</span>
}

export function CompaniesPage() {
  const { t, i18n } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editCompany, setEditCompany] = useState<CompanyWithBilling | null>(null)
  const [billingCompany, setBillingCompany] = useState<CompanyWithBilling | null>(null)
  const [modulesCompany, setModulesCompany] = useState<CompanyWithBilling | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<CompanyWithBilling>>('/super-admin/companies', { params: { page_size: 100 } })
      return data
    },
  })

  const suspendCompany = useMutation({
    mutationFn: async (id: number) => api.post(`/super-admin/companies/${id}/suspend`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })

  const activateCompany = useMutation({
    mutationFn: async (id: number) => api.post(`/super-admin/companies/${id}/activate`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })

  const sendReminder = useMutation({
    mutationFn: async (id: number) => api.post(`/super-admin/companies/${id}/billing/send-reminder`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })

  const overdueCount = data?.items.filter((c) => c.billing?.payment_status === 'overdue').length ?? 0

  return (
    <div>
      <PageHeader
        title={t('companies')}
        subtitle={t('companies_billing_help')}
        icon={Building2}
        accentIndex={2}
        actions={
          <Button onClick={() => setOpen(true)}>
            <Building2 className="me-2 h-4 w-4" />
            {t('add_company')}
          </Button>
        }
      />

      <div className="grid-stagger mb-6 grid gap-4 sm:grid-cols-3">
        <Card className="p-4">
          <p className="text-sm text-slate-500">{t('total_companies')}</p>
          <p className="text-2xl font-bold text-slate-900">{data?.total ?? 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-slate-500">{t('active_companies')}</p>
          <p className="text-2xl font-bold text-emerald-700">
            {data?.items.filter((c) => c.status === 'active' || c.status === 'trial').length ?? 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-slate-500">{t('overdue_payments')}</p>
          <p className="text-2xl font-bold text-red-600">{overdueCount}</p>
        </Card>
      </div>

      <Card>
        {isLoading ? (
          <LoadingState />
        ) : data?.items.length === 0 ? (
          <p className="text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[960px] text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-3 text-start font-medium">{t('companies')}</th>
                  <th className="pb-3 text-start font-medium">{t('subscription_plan')}</th>
                  <th className="pb-3 text-start font-medium">{t('payment_terms')}</th>
                  <th className="pb-3 text-start font-medium">{t('next_billing_date')}</th>
                  <th className="pb-3 text-start font-medium">{t('amount_due')}</th>
                  <th className="pb-3 text-start font-medium">{t('payment_status')}</th>
                  <th className="pb-3 text-start font-medium">{t('status')}</th>
                  <th className="pb-3 text-start font-medium">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((company) => {
                  const billing = company.billing
                  const planName = i18n.language === 'ar'
                    ? billing?.plan_name_ar || billing?.plan_name_en
                    : billing?.plan_name_en || billing?.plan_name_ar
                  return (
                    <tr key={company.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                      <td className="py-4">
                        <p className="font-semibold text-slate-900">
                          {i18n.language === 'ar' ? company.name_ar : company.name_en}
                        </p>
                        <p className="text-xs text-slate-500">{company.code}</p>
                      </td>
                      <td className="py-4">
                        <p>{planName || '—'}</p>
                        <p className="text-xs text-slate-500">{billing ? t(billing.billing_cycle) : ''}</p>
                      </td>
                      <td className="py-4">
                        {billing ? t('net_days', { days: billing.payment_terms_days }) : '—'}
                      </td>
                      <td className="py-4">{billing?.next_billing_date || '—'}</td>
                      <td className="py-4 font-medium">
                        {billing?.amount_due != null ? formatEGP(billing.amount_due) : '—'}
                      </td>
                      <td className="py-4">
                        {billing ? <PaymentStatusBadge status={billing.payment_status} t={t} /> : '—'}
                      </td>
                      <td className="py-4">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                          company.status === 'active' || company.status === 'trial'
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-red-50 text-red-700'
                        }`}>
                          {t(company.status)}
                        </span>
                      </td>
                      <td className="py-4">
                        <div className="flex flex-wrap gap-1.5">
                          <Button variant="secondary" onClick={() => setBillingCompany(company)}>
                            <CreditCard className="me-1 h-4 w-4" />{t('billing')}
                          </Button>
                          <Button
                            variant="secondary"
                            loading={sendReminder.isPending}
                            onClick={() => sendReminder.mutate(company.id)}
                          >
                            <Bell className="me-1 h-4 w-4" />{t('remind')}
                          </Button>
                          <Button variant="secondary" onClick={() => setEditCompany(company)}>
                            <Pencil className="me-1 h-4 w-4" />{t('edit')}
                          </Button>
                          <Button variant="secondary" onClick={() => setModulesCompany(company)}>
                            <SlidersHorizontal className="me-1 h-4 w-4" />
                          </Button>
                          {company.status === 'active' || company.status === 'trial' ? (
                            <Button variant="secondary" loading={suspendCompany.isPending} onClick={() => suspendCompany.mutate(company.id)}>
                              {t('suspend')}
                            </Button>
                          ) : (
                            <Button variant="secondary" loading={activateCompany.isPending} onClick={() => activateCompany.mutate(company.id)}>
                              {t('activate')}
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <CompanyFormModal open={open} onClose={() => { setOpen(false); qc.invalidateQueries({ queryKey: ['companies'] }) }} />
      <CompanyEditModal open={!!editCompany} company={editCompany} onClose={() => setEditCompany(null)} onSaved={() => qc.invalidateQueries({ queryKey: ['companies'] })} />
      <CompanyBillingModal open={!!billingCompany} company={billingCompany} onClose={() => setBillingCompany(null)} onSaved={() => qc.invalidateQueries({ queryKey: ['companies'] })} />
      {modulesCompany && (
        <CompanyModulesModal
          open={!!modulesCompany}
          companyId={modulesCompany.id}
          companyName={i18n.language === 'ar' ? modulesCompany.name_ar : modulesCompany.name_en}
          onClose={() => setModulesCompany(null)}
        />
      )}
    </div>
  )
}
