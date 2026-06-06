import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Pencil } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { SubscriptionPlanModal, type SubscriptionPlan } from '@/components/forms/SubscriptionPlanModal'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'

export function SubscriptionPlansPage() {
  const { t, i18n } = useTranslation()
  const { formatInteger, formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const [editPlan, setEditPlan] = useState<SubscriptionPlan | null>(null)

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['subscription-plans'],
    queryFn: async () => {
      const { data } = await api.get<SubscriptionPlan[]>('/super-admin/subscription-plans')
      return data
    },
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('subscriptions')}</h1>
      <p className="mb-6 text-sm text-slate-600">{t('subscriptions_help')}</p>
      <div className="grid gap-4 md:grid-cols-3">
        {isLoading ? (
          <p className="text-slate-500">{t('loading')}</p>
        ) : (
          plans.map((plan) => (
            <Card key={plan.id} className="flex flex-col">
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
              <p className="text-2xl font-bold text-primary-700">{formatEGP(plan.price_monthly)}<span className="text-sm font-normal text-slate-500">/{t('month')}</span></p>
              <ul className="mt-4 flex-1 space-y-1 text-sm text-slate-600">
                <li>{formatInteger(plan.max_users)} {t('users')}</li>
                <li>{formatInteger(plan.max_projects)} {t('projects')}</li>
                <li>{formatInteger(plan.max_storage_mb)} MB</li>
                <li>{formatInteger(plan.enabled_modules?.length ?? 0)} {t('features')}</li>
              </ul>
              <Button variant="secondary" className="mt-4 w-full" onClick={() => setEditPlan(plan)}>
                <Pencil className="me-2 h-4 w-4" />{t('edit_plan')}
              </Button>
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
    </div>
  )
}
