import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Settings, Shield, Save } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingState } from '@/components/ui/LoadingState'
import api from '@/lib/api'
import { cn } from '@/lib/utils'
import type { PortalFeatureCatalogItem } from '@/stores/portalFeaturesStore'

export function CompanyPortalSettingsPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [enabled, setEnabled] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['portal-features-admin'],
    queryFn: async () => {
      const { data: res } = await api.get<{
        portal_module_enabled: boolean
        enabled: string[]
        catalog: PortalFeatureCatalogItem[]
      }>('/modules/company/me/portal-features')
      return res
    },
  })

  useEffect(() => {
    if (data?.enabled) {
      setEnabled(new Set(data.enabled))
    }
  }, [data?.enabled])

  const toggle = (key: string, core?: boolean) => {
    if (core) return
    setEnabled((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const save = async () => {
    setSaving(true)
    setMessage('')
    try {
      await api.put('/modules/company/me/portal-features', {
        enabled_features: Array.from(enabled),
      })
      setMessage(t('portal_settings_saved'))
      qc.invalidateQueries({ queryKey: ['portal-features-admin'] })
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <LoadingState />

  if (!data?.portal_module_enabled) {
    return (
      <div>
        <PageHeader
          title={t('portal_settings')}
          subtitle={t('portal_settings_help')}
          icon={Settings}
          accentIndex={4}
        />
        <Card className="border-amber-200 bg-amber-50/50">
          <div className="flex items-start gap-3">
            <Shield className="mt-0.5 h-5 w-5 text-amber-600" />
            <p className="text-sm text-amber-900">{t('company_features_contact_superadmin')}</p>
          </div>
        </Card>
      </div>
    )
  }

  const catalog = data.catalog ?? []

  return (
    <div>
      <PageHeader
        title={t('portal_settings')}
        subtitle={t('portal_settings_help')}
        icon={Settings}
        accentIndex={4}
        actions={
          <Button onClick={save} loading={saving}>
            <Save className="me-2 h-4 w-4" />
            {t('save')}
          </Button>
        }
      />

      {message && (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </div>
      )}

      <Card className="mb-6 border-blue-200 bg-blue-50/50">
        <div className="flex items-start gap-3">
          <Shield className="mt-0.5 h-5 w-5 text-blue-600" />
          <p className="text-sm text-blue-800">{t('portal_settings_help')}</p>
        </div>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2">
        {catalog.map((feat) => {
          const on = enabled.has(feat.key)
          const name = i18n.language === 'ar' ? feat.name_ar : feat.name_en
          const desc = i18n.language === 'ar' ? feat.description_ar : feat.description_en
          return (
            <button
              key={feat.key}
              type="button"
              disabled={feat.core}
              onClick={() => toggle(feat.key, feat.core)}
              className={cn(
                'rounded-xl border px-4 py-4 text-start transition',
                on ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200 bg-white hover:bg-slate-50',
                feat.core && 'cursor-default opacity-90',
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-slate-900">{name}</span>
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    on ? 'bg-emerald-200 text-emerald-900' : 'bg-slate-200 text-slate-600',
                  )}
                >
                  {on ? t('enabled') : t('disabled')}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{desc}</p>
              {feat.core && (
                <p className="mt-2 text-xs text-slate-500">({t('required')})</p>
              )}
            </button>
          )
        })}
      </div>

      <p className="mt-6 text-sm text-slate-500">
        {t('portal_buyer_link')}{' '}
        <a href="/login" className="font-medium text-primary-700 hover:underline" target="_blank" rel="noreferrer">
          /login
        </a>
      </p>
    </div>
  )
}
