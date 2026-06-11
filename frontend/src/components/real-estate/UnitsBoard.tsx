import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Plus } from 'lucide-react'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

const STATUS_STYLES: Record<string, string> = {
  available: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  reserved: 'bg-amber-100 text-amber-800 border-amber-300',
  contracted: 'bg-blue-100 text-blue-800 border-blue-300',
  sold: 'bg-violet-100 text-violet-800 border-violet-300',
  delivered: 'bg-slate-100 text-slate-800 border-slate-300',
  blocked: 'bg-red-100 text-red-800 border-red-300',
}

interface UnitCard {
  id: number
  unit_code: string
  unit_number: string
  unit_type: string
  price: number
  base_price?: number
  adjustment_percent?: number
  area_sqm: number
}

interface UnitsBoardProps {
  onUnitClick?: (unitId: number, status: string) => void
}

export function UnitsBoard({ onUnitClick }: UnitsBoardProps) {
  const { t } = useTranslation()
  const { formatEGP, formatInteger, formatNumber, localizeDigits } = useFormatNumber()
  const { data, isLoading } = useQuery({
    queryKey: ['units-board'],
    queryFn: async () => {
      const { data } = await api.get<Record<string, UnitCard[]>>('/projects/units/board')
      return data
    },
  })

  if (isLoading) return <p className="text-slate-500">{t('loading')}</p>

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-500">{t('units_board_help')}</p>
      {Object.entries(data ?? {}).map(([status, units]) => (
        <div key={status}>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold capitalize">
            <span className={cn('rounded-full px-2.5 py-1 text-xs', STATUS_STYLES[status] ?? 'bg-slate-100')}>
              {status} ({formatInteger(units.length)})
            </span>
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {units.map((u) => (
              <button
                key={u.id}
                type="button"
                onClick={() => onUnitClick?.(u.id, status)}
                className={cn(
                  'rounded-xl border-2 p-4 text-start transition hover:shadow-md',
                  STATUS_STYLES[status] ?? 'border-slate-200',
                  onUnitClick && 'cursor-pointer hover:scale-[1.02]',
                )}
              >
                <p className="font-bold">{u.unit_code}</p>
                <p className="text-xs opacity-75">#{localizeDigits(u.unit_number)} · {u.unit_type}</p>
                <div className="mt-2">
                  {u.base_price && u.adjustment_percent && u.adjustment_percent > 0 && u.base_price !== u.price ? (
                    <>
                      <p className="text-xs text-slate-400 line-through">{formatEGP(u.base_price)}</p>
                      <p className="text-sm font-semibold text-emerald-800">
                        {formatEGP(u.price)}
                        <span className="ms-1 text-xs font-normal text-emerald-600">
                          (+{localizeDigits(String(u.adjustment_percent))}%)
                        </span>
                      </p>
                    </>
                  ) : (
                    <p className="text-sm font-semibold">{formatEGP(u.price)}</p>
                  )}
                </div>
                <p className="text-xs opacity-75">{formatNumber(u.area_sqm)} m²</p>
                {status === 'available' && onUnitClick && (
                  <p className="mt-2 flex items-center gap-1 text-xs font-medium text-emerald-700">
                    <Plus className="h-3 w-3" /> {t('reserve_unit')}
                  </p>
                )}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
