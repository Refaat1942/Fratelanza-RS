import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { CreditCard, Download, Pencil, Plus } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingState } from '@/components/ui/LoadingState'
import { Button } from '@/components/ui/Button'
import { SubscriptionPlanModal, type SubscriptionPlan } from '@/components/forms/SubscriptionPlanModal'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { formatPlanLimit } from '@/lib/planLimits'

export function SubscriptionPlansPage() {
  const { t, i18n } = useTranslation()
  const { formatInteger, formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const [editPlan, setEditPlan] = useState<SubscriptionPlan | null>(null)
  const [createOpen, setCreateOpen] = useState(false)

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['subscription-plans'],
    queryFn: async () => {
      const { data } = await api.get<SubscriptionPlan[]>('/super-admin/subscription-plans')
      return data
    },
  })

  const downloadBrochure = async () => {
    const { data } = await api.get('/super-admin/subscription-plans/brochure.pdf', { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = 'fratelanza-subscription-plans.pdf'
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadPlanPdf = async (plan: SubscriptionPlan) => {
    const { data } = await api.get(`/super-admin/subscription-plans/${plan.id}/brochure.pdf`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `fratelanza-plan-${plan.code}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <PageHeader
        title={t('subscriptions')}
        subtitle={t('subscriptions_help')}
        icon={CreditCard}
        accentIndex={4}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => setCreateOpen(true)}>
              <Plus className="me-2 h-4 w-4" />
              {t('add_subscription_plan')}
            </Button>
            <Button variant="secondary" onClick={downloadBrochure}>
              <Download className="me-2 h-4 w-4" />
              {t('download_plans_pdf')}
            </Button>
          </div>
        }
      />
      <div className="grid-stagger grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {isLoading ? (
          <LoadingState />
        ) : (
          plans.map((plan) => (
            <Card key={plan.id} className="flex flex-col" gradient>
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    {i18n.language === 'ar' ? plan.name_ar : plan.name_en}
                  </h3>
                  <p className="text-xs text-slate-500">{plan.code}</p>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs ${plan.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                  {plan.is_active ? t('active') : t('inactive')}
                </span>
              </div>
              {(plan.description_en || plan.description_ar) && (
                <p className="mb-3 line-clamp-2 text-sm text-slate-600">
                  {i18n.language === 'ar' ? plan.description_ar : plan.description_en}
                </p>
              )}
              <div className="space-y-1">
                {plan.billing_type === 'one_time' ? (
                  <>
                    <p className="text-2xl font-bold text-primary-700">
                      {formatEGP(plan.price_one_time ?? 0)}
                      <span className="text-sm font-normal text-slate-500"> {t('one_time_payment')}</span>
                    </p>
                    {(plan.hosting_fee_monthly ?? 0) > 0 && (
                      <p className="text-sm text-slate-600">
                        + {formatEGP(plan.hosting_fee_monthly)} / {t('month')} {t('hosting_fee_label')}
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p className="text-2xl font-bold text-primary-700">
                      {formatEGP(plan.price_monthly)}
                      <span className="text-sm font-normal text-slate-500">/{t('month')}</span>
                    </p>
                    <p className="text-sm text-slate-600">
                      {formatEGP(plan.price_yearly)} / {t('yearly')}
                    </p>
                  </>
                )}
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {(plan.support_months ?? 0) > 0 && (
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                    {t('support_months_badge', { months: plan.support_months })}
                  </span>
                )}
                {plan.includes_hosting ? (
                  <span className="rounded-full bg-violet-50 px-2 py-0.5 text-xs text-violet-700">{t('with_hosting')}</span>
                ) : (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{t('software_only')}</span>
                )}
              </div>
              <ul className="mt-4 flex-1 space-y-1 text-sm text-slate-600">
                <li>{formatPlanLimit(plan.max_users, t('unlimited'))} {t('users')}</li>
                <li>{formatPlanLimit(plan.max_projects, t('unlimited'))} {t('projects')}</li>
                <li>{formatPlanLimit(plan.max_storage_mb, t('unlimited'))} {plan.max_storage_mb > 0 ? 'MB' : ''}</li>
                <li>{formatInteger(plan.enabled_modules?.length ?? 0)} {t('features')}</li>
              </ul>
              <div className="mt-4 flex flex-col gap-2">
                <Button variant="secondary" className="w-full" onClick={() => setEditPlan(plan)}>
                  <Pencil className="me-2 h-4 w-4" />{t('edit_plan')}
                </Button>
                <Button variant="ghost" className="w-full" onClick={() => downloadPlanPdf(plan)}>
                  <Download className="me-2 h-4 w-4" />{t('download_plan_pdf')}
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>
      <SubscriptionPlanModal
        open={!!editPlan}
        plan={editPlan}
        onClose={() => setEditPlan(null)}
        onSaved={() => qc.invalidateQueries({ queryKey: ['subscription-plans'] })}
      />
      <SubscriptionPlanModal
        open={createOpen}
        plan={null}
        createMode
        onClose={() => setCreateOpen(false)}
        onSaved={() => qc.invalidateQueries({ queryKey: ['subscription-plans'] })}
      />
    </div>
  )
}
