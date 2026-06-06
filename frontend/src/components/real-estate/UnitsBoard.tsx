import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
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
  area_sqm: number
}

export function UnitsBoard() {
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
      {Object.entries(data ?? {}).map(([status, units]) => (
        <div key={status}>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold capitalize">
            <span className={cn('rounded-full px-2.5 py-1 text-xs', STATUS_STYLES[status] ?? 'bg-slate-100')}>
              {status} ({formatInteger(units.length)})
            </span>
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {units.map((u) => (
              <div key={u.id} className={cn('rounded-xl border-2 p-4 transition hover:shadow-md', STATUS_STYLES[status] ?? 'border-slate-200')}>
                <p className="font-bold">{u.unit_code}</p>
                <p className="text-xs opacity-75">#{localizeDigits(u.unit_number)} · {u.unit_type}</p>
                <p className="mt-2 text-sm font-semibold">{formatEGP(u.price)}</p>
                <p className="text-xs opacity-75">{formatNumber(u.area_sqm)} m²</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
