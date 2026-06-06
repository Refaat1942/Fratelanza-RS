import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import type { ModuleCatalogItem } from '@/stores/modulesStore'
import { cn } from '@/lib/utils'

interface CompanyModulesModalProps {
  open: boolean
  onClose: () => void
  companyId: number
  companyName: string
}

export function CompanyModulesModal({ open, onClose, companyId, companyName }: CompanyModulesModalProps) {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [catalog, setCatalog] = useState<ModuleCatalogItem[]>([])
  const [enabled, setEnabled] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!open || !companyId) return
    setLoading(true)
    api.get(`/modules/company/${companyId}`)
      .then(({ data }) => {
        setCatalog(data.catalog ?? [])
        setEnabled(new Set(data.enabled ?? []))
      })
      .finally(() => setLoading(false))
  }, [open, companyId])

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

  const selectAll = () => setEnabled(new Set(catalog.map((m) => m.key)))
  const selectNone = () => setEnabled(new Set(catalog.filter((m) => m.core).map((m) => m.key)))

  const save = async () => {
    setSaving(true)
    try {
      await api.put(`/modules/company/${companyId}`, {
        enabled_modules: Array.from(enabled),
      })
      qc.invalidateQueries({ queryKey: ['companies'] })
      onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('manage_company_modules')} className="max-w-2xl">
      <p className="mb-4 text-sm text-slate-600">
        {t('manage_modules_help', { company: companyName })}
      </p>
      <div className="mb-4 flex gap-2">
        <Button type="button" variant="secondary" onClick={selectAll}>{t('enable_all')}</Button>
        <Button type="button" variant="secondary" onClick={selectNone}>{t('disable_optional')}</Button>
      </div>
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
                        mod.core && 'cursor-not-allowed opacity-70',
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={on}
                        disabled={mod.core}
                        onChange={() => toggle(mod.key, mod.core)}
                      />
                      <span>{name}</span>
                      {mod.core && <span className="text-xs text-slate-400">({t('required')})</span>}
                    </label>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="mt-6 flex gap-3">
        <Button onClick={save} loading={saving}>{t('save')}</Button>
        <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
      </div>
    </Modal>
  )
}
