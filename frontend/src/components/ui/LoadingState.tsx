import { useTranslation } from 'react-i18next'

export function LoadingState() {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className="loading-spinner" />
      <p className="animate-pulse-soft text-sm font-medium text-slate-500">{t('loading')}</p>
    </div>
  )
}
