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
        <Button variant="ghost" onClick={onEdit} title={t('edit')} className="!px-2 !py-1.5">
          <Pencil className="h-4 w-4" />
        </Button>
      )}
      {onDelete && (
        <Button variant="ghost" onClick={onDelete} title={t('delete')} className="!px-2 !py-1.5 text-red-600 hover:text-red-700">
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}
