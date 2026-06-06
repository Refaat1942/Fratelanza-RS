import { useTranslation } from 'react-i18next'
import { Card } from '@/components/ui/Card'
import { Construction } from 'lucide-react'

interface PlaceholderPageProps {
  titleKey: string
}

export function PlaceholderPage({ titleKey }: PlaceholderPageProps) {
  const { t } = useTranslation()
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t(titleKey)}</h1>
      <Card className="flex flex-col items-center justify-center py-16 text-center">
        <Construction className="mb-4 h-12 w-12 text-slate-300" />
        <p className="text-lg font-medium text-slate-600">{t(titleKey)}</p>
        <p className="mt-2 text-sm text-slate-400">Module ready — API & database schema configured</p>
      </Card>
    </div>
  )
}
