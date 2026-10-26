import { useTranslation } from 'react-i18next'
import { FlaskConical } from 'lucide-react'
import { usePermissionsStore } from '@/stores/permissionsStore'

/** Always-visible label for demo tenants (the server enforces demo restrictions independently). */
export function DemoBanner() {
  const { t, i18n } = useTranslation()
  const data = usePermissionsStore((s) => s.data)
  if (!data?.is_demo) return null
  const expires = data.demo?.expires_at
    ? new Intl.DateTimeFormat(i18n.language === 'ar' ? 'ar-EG' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(data.demo.expires_at))
    : null
  return (
    <div className="border-b border-violet-300 bg-gradient-to-r from-violet-600 to-fuchsia-600 px-4 py-2 text-sm text-white" role="status">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-2 text-center">
        <FlaskConical className="h-4 w-4 shrink-0" />
        <span className="font-semibold">{t('re.demo.banner')}</span>
        {data.demo?.prospect_name && <span className="opacity-90">— {data.demo.prospect_name}</span>}
        {expires && <span className="opacity-90">({t('re.demo.expires')}: {expires})</span>}
      </div>
    </div>
  )
}
