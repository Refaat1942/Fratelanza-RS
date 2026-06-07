import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { BarChart3 } from 'lucide-react'
import { Button } from './Button'

interface ReportLinkButtonProps {
  reportKey: string
  variant?: 'primary' | 'secondary' | 'ghost'
}

export function ReportLinkButton({ reportKey, variant = 'secondary' }: ReportLinkButtonProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  return (
    <Button variant={variant} onClick={() => navigate(`/reports?report=${reportKey}`)}>
      <BarChart3 className="me-2 h-4 w-4" />
      {t('view_report')}
    </Button>
  )
}
