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
  price_monthly: number
  price_yearly: number
  max_users: number
  max_projects: number
  max_storage_mb: number
  enabled_modules: string[]
  is_active: boolean
}

interface SubscriptionPlanModalProps {
  open: boolean
  onClose: () => void
  plan: SubscriptionPlan | null
  onSaved: () => void
}

export function SubscriptionPlanModal({ open, onClose, plan, onSaved }: SubscriptionPlanModalProps) {
  const { t, i18n } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [catalog, setCatalog] = useState<ModuleCatalogItem[]>([])
  const [form, setForm] = useState({
    name_ar: '',
    name_en: '',
    price_monthly: '',
    price_yearly: '',
    max_users: '',
    max_projects: '',
    max_storage_mb: '',
    is_active: true,
  })
  const [enabled, setEnabled] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (open) {
      api.get('/modules/catalog').then(({ data }) => setCatalog(data.modules ?? []))
    }
  }, [open])

  useEffect(() => {
    if (plan && open) {
      setForm({
        name_ar: plan.name_ar,
        name_en: plan.name_en,
        price_monthly: String(plan.price_monthly),
        price_yearly: String(plan.price_yearly),
        max_users: String(plan.max_users),
        max_projects: String(plan.max_projects),
        max_storage_mb: String(plan.max_storage_mb),
        is_active: plan.is_active,
      })
      setEnabled(new Set(plan.enabled_modules ?? []))
    }
  }, [plan, open])

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
    if (!plan) return
    setLoading(true)
    try {
      await api.put(`/super-admin/subscription-plans/${plan.id}`, {
        name_ar: form.name_ar,
        name_en: form.name_en,
        price_monthly: Number(form.price_monthly),
        price_yearly: Number(form.price_yearly),
        max_users: Number(form.max_users),
        max_projects: Number(form.max_projects),
        max_storage_mb: Number(form.max_storage_mb),
        is_active: form.is_active,
        enabled_modules: Array.from(enabled),
      })
      onSaved()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('edit_subscription_plan')} className="max-w-2xl">
      {plan && (
        <form onSubmit={submit} className="space-y-4">
          <p className="text-sm text-slate-500">{t('plan_code')}: <strong>{plan.code}</strong></p>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
            <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t('price_monthly')} type="number" value={form.price_monthly} onChange={(e) => setForm({ ...form, price_monthly: e.target.value })} />
            <Input label={t('price_yearly')} type="number" value={form.price_yearly} onChange={(e) => setForm({ ...form, price_yearly: e.target.value })} />
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Input label={t('max_users')} type="number" value={form.max_users} onChange={(e) => setForm({ ...form, max_users: e.target.value })} />
            <Input label={t('max_projects')} type="number" value={form.max_projects} onChange={(e) => setForm({ ...form, max_projects: e.target.value })} />
            <Input label={t('max_storage_mb')} type="number" value={form.max_storage_mb} onChange={(e) => setForm({ ...form, max_storage_mb: e.target.value })} />
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
      )}
    </Modal>
  )
}
