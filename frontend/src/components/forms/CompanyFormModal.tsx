import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import type { SubscriptionPlan } from '@/components/forms/SubscriptionPlanModal'

interface CompanyFormModalProps {
  open: boolean
  onClose: () => void
}

export function CompanyFormModal({ open, onClose }: CompanyFormModalProps) {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    name_ar: '',
    name_en: '',
    code: '',
    email: '',
    phone: '',
    city: '',
    country: 'Egypt',
    plan_id: '' as string | number,
    start_trial: true,
    admin_email: '',
    admin_password: '',
    admin_name_ar: '',
    admin_name_en: '',
  })

  const { data: plans = [] } = useQuery({
    queryKey: ['subscription-plans'],
    queryFn: async () => {
      const { data } = await api.get<SubscriptionPlan[]>('/super-admin/subscription-plans')
      return data
    },
    enabled: open,
  })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/super-admin/companies', {
        ...form,
        plan_id: form.plan_id ? Number(form.plan_id) : undefined,
        start_trial: form.start_trial,
      })
      qc.invalidateQueries({ queryKey: ['companies'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('add_company')} className="max-w-xl">
      <form onSubmit={submit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
          <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        </div>
        <Input label="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
        <Input label={t('email')} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <Input label={t('mobile')} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />

        <hr className="border-slate-200" />
        <p className="text-sm font-medium text-slate-600">{t('subscription_plan')}</p>
        <label className="block text-sm">
          <span className="mb-1 block text-slate-600">{t('subscription_plan')}</span>
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={form.plan_id}
            onChange={(e) => setForm({ ...form, plan_id: e.target.value })}
            required={form.start_trial}
          >
            <option value="">{t('select_plan')}</option>
            {plans.map((plan) => (
              <option key={plan.id} value={plan.id}>
                {i18n.language === 'ar' ? plan.name_ar : plan.name_en}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.start_trial}
            onChange={(e) => setForm({ ...form, start_trial: e.target.checked })}
            className="rounded border-slate-300"
          />
          {t('start_trial_14_days')}
        </label>
        {form.start_trial && (
          <p className="text-xs text-slate-500">{t('trial_help')}</p>
        )}

        <hr className="border-slate-200" />
        <p className="text-sm font-medium text-slate-600">{t('company_admin')}</p>
        <Input label={t('email')} value={form.admin_email} onChange={(e) => setForm({ ...form, admin_email: e.target.value })} />
        <Input label={t('password')} type="password" value={form.admin_password} onChange={(e) => setForm({ ...form, admin_password: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
