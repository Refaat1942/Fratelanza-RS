import { Pencil, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from './Button'

interface RowActionsProps {
  onEdit?: () => void
  onDelete?: () => void
  extra?: React.ReactNode
}

export function RowActions({ onEdit, onDelete, extra }: RowActionsProps) {
  const { t } = useTranslation()
  return (
    <div className="flex items-center gap-1">
      {extra}
      {onEdit && (
        <Button variant="secondary" onClick={onEdit} title={t('edit')} className="!px-2 !py-1.5 text-xs">
          <Pencil className="h-3.5 w-3.5 me-1" />{t('edit')}
        </Button>
      )}
      {onDelete && (
        <Button variant="secondary" onClick={onDelete} title={t('delete')} className="!px-2 !py-1.5 text-xs text-red-600 hover:text-red-700">
          <Trash2 className="h-3.5 w-3.5 me-1" />{t('delete')}
        </Button>
      )}
    </div>
  )
}
