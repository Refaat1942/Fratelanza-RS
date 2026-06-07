import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import type { ModuleCatalogItem } from '@/stores/modulesStore'
import { cn } from '@/lib/utils'

interface UserFeaturesModalProps {
  open: boolean
  onClose: () => void
  userId: number
  userName: string
  onSaved: () => void
}

export function UserFeaturesModal({ open, onClose, userId, userName, onSaved }: UserFeaturesModalProps) {
  const { t, i18n } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [inheritsCompany, setInheritsCompany] = useState(true)
  const [catalog, setCatalog] = useState<ModuleCatalogItem[]>([])
  const [companyModules, setCompanyModules] = useState<Set<string>>(new Set())
  const [enabled, setEnabled] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!open || !userId) return
    setLoading(true)
    api.get(`/users/${userId}/modules`)
      .then(({ data }) => {
        setCatalog(data.catalog ?? [])
        setCompanyModules(new Set(data.company_modules ?? []))
        setInheritsCompany(data.inherits_company ?? true)
        setEnabled(new Set(data.effective_modules ?? data.company_modules ?? []))
      })
      .finally(() => setLoading(false))
  }, [open, userId])

  const grouped = useMemo(() => {
    const map = new Map<string, ModuleCatalogItem[]>()
    for (const mod of catalog.filter((m) => companyModules.has(m.key))) {
      const cat = i18n.language === 'ar' ? mod.category_ar : mod.category_en
      if (!map.has(cat)) map.set(cat, [])
      map.get(cat)!.push(mod)
    }
    return map
  }, [catalog, companyModules, i18n.language])

  const toggle = (key: string, core?: boolean) => {
    if (core || inheritsCompany) return
    setEnabled((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const enableCustom = () => {
    setInheritsCompany(false)
    setEnabled(new Set(companyModules))
  }

  const resetToCompany = async () => {
    setSaving(true)
    try {
      await api.delete(`/users/${userId}/modules`)
      onSaved()
      onClose()
    } finally {
      setSaving(false)
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      await api.put(`/users/${userId}/modules`, {
        enabled_modules: Array.from(enabled),
      })
      onSaved()
      onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('user_feature_access')} className="max-w-2xl">
      <p className="mb-4 text-sm text-slate-600">
        {t('user_features_help', { user: userName })}
      </p>
      {inheritsCompany && (
        <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
          {t('user_inherits_company_modules')}
          <Button type="button" variant="secondary" className="mt-2" onClick={enableCustom}>
            {t('customize_user_features')}
          </Button>
        </div>
      )}
      {loading ? (
        <p className="text-slate-500">{t('loading')}</p>
      ) : (
        <div className="max-h-[50vh] space-y-5 overflow-y-auto">
          {Array.from(grouped.entries()).map(([category, mods]) => (
            <div key={category}>
              <p className="mb-2 text-sm font-semibold text-slate-800">{category}</p>
              <div className="grid gap-2 sm:grid-cols-2">
                {mods.map((mod) => {
                  const on = enabled.has(mod.key)
                  const name = i18n.language === 'ar' ? mod.name_ar : mod.name_en
                  return (
                    <label
                      key={mod.key}
                      className={cn(
                        'flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm',
                        on ? 'border-primary-300 bg-primary-50' : 'border-slate-200 bg-white',
                        (mod.core || inheritsCompany) && 'cursor-not-allowed opacity-70',
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={on}
                        disabled={mod.core || inheritsCompany}
                        onChange={() => toggle(mod.key, mod.core)}
                      />
                      <span>{name}</span>
                    </label>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="mt-6 flex flex-wrap gap-3">
        {!inheritsCompany && <Button onClick={save} loading={saving}>{t('save')}</Button>}
        {!inheritsCompany && (
          <Button type="button" variant="secondary" onClick={resetToCompany} loading={saving}>
            {t('reset_to_company_defaults')}
          </Button>
        )}
        <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
      </div>
    </Modal>
  )
}
