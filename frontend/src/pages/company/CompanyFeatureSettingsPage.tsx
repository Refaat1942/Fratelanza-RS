import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Settings, Shield } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingState } from '@/components/ui/LoadingState'
import api from '@/lib/api'

export function CompanyFeatureSettingsPage() {
  const { t, i18n } = useTranslation()

  const { data, isLoading } = useQuery({
    queryKey: ['company-modules-me'],
    queryFn: async () => {
      const { data: res } = await api.get<{
        enabled: string[]
        catalog: { key: string; name_en: string; name_ar: string; core: boolean }[]
      }>('/modules/company/me')
      return res
    },
  })

  const enabledSet = new Set(data?.enabled ?? [])
  const modules = data?.catalog ?? []

  return (
    <div>
      <PageHeader
        title={t('feature_settings')}
        subtitle={t('feature_settings_help')}
        icon={Settings}
        accentIndex={3}
      />
      <Card className="mb-6 border-blue-200 bg-blue-50/50">
        <div className="flex items-start gap-3">
          <Shield className="mt-0.5 h-5 w-5 text-blue-600" />
          <div>
            <p className="font-medium text-blue-900">{t('company_features_note')}</p>
            <p className="mt-1 text-sm text-blue-800">{t('company_features_contact_superadmin')}</p>
          </div>
        </div>
      </Card>
      {isLoading ? (
        <LoadingState />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((mod) => {
            const on = enabledSet.has(mod.key)
            const name = i18n.language === 'ar' ? mod.name_ar : mod.name_en
            return (
              <div
                key={mod.key}
                className={`rounded-lg border px-4 py-3 text-sm ${
                  on ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-slate-200 bg-slate-50 text-slate-500'
                }`}
              >
                <span className="font-medium">{name}</span>
                {mod.core && <span className="ms-2 text-xs opacity-70">({t('required')})</span>}
                <span className="mt-1 block text-xs">{on ? t('enabled') : t('disabled')}</span>
              </div>
            )
          })}
        </div>
      )}
      <p className="mt-6 text-sm text-slate-600">{t('per_user_features_hint')}</p>
    </div>
  )
}
