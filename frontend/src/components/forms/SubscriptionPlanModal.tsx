import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import type { ModuleCatalogItem } from '@/stores/modulesStore'
import { cn } from '@/lib/utils'

export interface SubscriptionPlan {
  id: number
  name_ar: string
  name_en: string
  code: string
  description_ar?: string
  description_en?: string
  billing_type?: string
  price_monthly: number
  price_yearly: number
  price_one_time?: number
  hosting_fee_monthly?: number
  max_users: number
  max_projects: number
  max_storage_mb: number
  support_months?: number
  includes_hosting?: boolean
  enabled_modules: string[]
  sort_order?: number
  is_active: boolean
}

interface SubscriptionPlanModalProps {
  open: boolean
  onClose: () => void
  plan: SubscriptionPlan | null
  createMode?: boolean
  onSaved: () => void
}

export function SubscriptionPlanModal({ open, onClose, plan, createMode = false, onSaved }: SubscriptionPlanModalProps) {
  const { t, i18n } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [catalog, setCatalog] = useState<ModuleCatalogItem[]>([])
  const [form, setForm] = useState({
    code: '',
    name_ar: '',
    name_en: '',
    description_ar: '',
    description_en: '',
    billing_type: 'recurring',
    price_monthly: '',
    price_yearly: '',
    price_one_time: '',
    hosting_fee_monthly: '',
    max_users: '',
    max_projects: '',
    max_storage_mb: '',
    support_months: '0',
    includes_hosting: false,
    sort_order: '0',
    is_active: true,
  })
  const [enabled, setEnabled] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (open) {
      api.get('/modules/catalog').then(({ data }) => setCatalog(data.modules ?? []))
    }
  }, [open])

  useEffect(() => {
    if (createMode && open) {
      setForm({
        code: '',
        name_ar: '',
        name_en: '',
        description_ar: '',
        description_en: '',
        billing_type: 'recurring',
        price_monthly: '',
        price_yearly: '',
        price_one_time: '',
        hosting_fee_monthly: '',
        max_users: '10',
        max_projects: '5',
        max_storage_mb: '5120',
        support_months: '0',
        includes_hosting: false,
        sort_order: '0',
        is_active: true,
      })
      setEnabled(new Set())
      return
    }
    if (plan && open) {
      setForm({
        code: plan.code,
        name_ar: plan.name_ar,
        name_en: plan.name_en,
        description_ar: plan.description_ar ?? '',
        description_en: plan.description_en ?? '',
        billing_type: plan.billing_type ?? 'recurring',
        price_monthly: String(plan.price_monthly),
        price_yearly: String(plan.price_yearly),
        price_one_time: String(plan.price_one_time ?? 0),
        hosting_fee_monthly: String(plan.hosting_fee_monthly ?? 0),
        max_users: String(plan.max_users),
        max_projects: String(plan.max_projects),
        max_storage_mb: String(plan.max_storage_mb),
        support_months: String(plan.support_months ?? 0),
        includes_hosting: plan.includes_hosting ?? false,
        sort_order: String(plan.sort_order ?? 0),
        is_active: plan.is_active,
      })
      setEnabled(new Set(plan.enabled_modules ?? []))
    }
  }, [plan, open, createMode])

  const grouped = useMemo(() => {
    const map = new Map<string, ModuleCatalogItem[]>()
    for (const mod of catalog) {
      const cat = i18n.language === 'ar' ? mod.category_ar : mod.category_en
      if (!map.has(cat)) map.set(cat, [])
      map.get(cat)!.push(mod)
    }
    return map
  }, [catalog, i18n.language])

  const toggle = (key: string, core?: boolean) => {
    if (core) return
    setEnabled((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        name_ar: form.name_ar,
        name_en: form.name_en,
        description_ar: form.description_ar || undefined,
        description_en: form.description_en || undefined,
        billing_type: form.billing_type,
        price_monthly: Number(form.price_monthly),
        price_yearly: Number(form.price_yearly),
        price_one_time: Number(form.price_one_time),
        hosting_fee_monthly: Number(form.hosting_fee_monthly),
        max_users: Number(form.max_users),
        max_projects: Number(form.max_projects),
        max_storage_mb: Number(form.max_storage_mb),
        support_months: Number(form.support_months),
        includes_hosting: form.includes_hosting,
        sort_order: Number(form.sort_order),
        is_active: form.is_active,
        enabled_modules: Array.from(enabled),
      }
      if (createMode) {
        await api.post('/super-admin/subscription-plans', { ...payload, code: form.code.trim().toLowerCase() })
      } else if (plan) {
        await api.put(`/super-admin/subscription-plans/${plan.id}`, payload)
      }
      onSaved()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  const isOpen = open && (createMode || !!plan)

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title={createMode ? t('add_subscription_plan') : t('edit_subscription_plan')}
      className="max-w-2xl"
    >
      <form onSubmit={submit} className="space-y-4">
        {createMode ? (
          <Input
            label={t('plan_code')}
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') })}
            required
            placeholder="starter"
          />
        ) : plan ? (
          <p className="text-sm text-slate-500">{t('plan_code')}: <strong>{plan.code}</strong></p>
        ) : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
          <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">{t('description_ar')}</label>
            <textarea className="input-field min-h-[72px]" value={form.description_ar} onChange={(e) => setForm({ ...form, description_ar: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">{t('description_en')}</label>
            <textarea className="input-field min-h-[72px]" value={form.description_en} onChange={(e) => setForm({ ...form, description_en: e.target.value })} />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">{t('billing_type')}</label>
          <select className="input-field" value={form.billing_type} onChange={(e) => setForm({ ...form, billing_type: e.target.value })}>
            <option value="recurring">{t('billing_recurring')}</option>
            <option value="one_time">{t('billing_one_time')}</option>
          </select>
        </div>
        {form.billing_type === 'one_time' ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t('price_one_time')} type="number" min={0} value={form.price_one_time} onChange={(e) => setForm({ ...form, price_one_time: e.target.value })} />
            <Input label={t('hosting_fee_monthly')} type="number" min={0} value={form.hosting_fee_monthly} onChange={(e) => setForm({ ...form, hosting_fee_monthly: e.target.value })} />
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t('price_monthly')} type="number" value={form.price_monthly} onChange={(e) => setForm({ ...form, price_monthly: e.target.value })} />
            <Input label={t('price_yearly')} type="number" value={form.price_yearly} onChange={(e) => setForm({ ...form, price_yearly: e.target.value })} />
          </div>
        )}
        <p className="text-xs text-slate-500">{t('unlimited_hint')}</p>
        <div className="grid gap-4 sm:grid-cols-4">
          <Input label={t('max_users')} type="number" min={0} value={form.max_users} onChange={(e) => setForm({ ...form, max_users: e.target.value })} />
          <Input label={t('max_projects')} type="number" min={0} value={form.max_projects} onChange={(e) => setForm({ ...form, max_projects: e.target.value })} />
          <Input label={t('max_storage_mb')} type="number" min={0} value={form.max_storage_mb} onChange={(e) => setForm({ ...form, max_storage_mb: e.target.value })} />
          <Input label={t('sort_order')} type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: e.target.value })} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label={t('support_months')} type="number" min={0} value={form.support_months} onChange={(e) => setForm({ ...form, support_months: e.target.value })} />
          <label className="flex items-center gap-2 self-end text-sm">
            <input type="checkbox" checked={form.includes_hosting} onChange={(e) => setForm({ ...form, includes_hosting: e.target.checked })} />
            {t('includes_hosting')}
          </label>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
          {t('active')}
        </label>
        <div>
          <p className="mb-2 text-sm font-medium text-slate-900">{t('plan_features')}</p>
          <div className="max-h-48 space-y-3 overflow-y-auto rounded-lg border border-slate-200 p-3">
            {Array.from(grouped.entries()).map(([category, mods]) => (
              <div key={category}>
                <p className="mb-1 text-xs font-semibold text-slate-600">{category}</p>
                <div className="grid gap-1 sm:grid-cols-2">
                  {mods.map((mod) => (
                    <label key={mod.key} className={cn('flex items-center gap-2 text-xs', mod.core && 'opacity-70')}>
                      <input type="checkbox" checked={enabled.has(mod.key)} disabled={mod.core} onChange={() => toggle(mod.key, mod.core)} />
                      {i18n.language === 'ar' ? mod.name_ar : mod.name_en}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-3">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
