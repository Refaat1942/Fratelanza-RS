import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, FileSignature, Wallet, AlertTriangle, Landmark, Receipt, Users, TrendingUp, Search, ShoppingBag, KeyRound, Building } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import api from '@/lib/api'
import { useFormatNumber } from '@/hooks/useFormatNumber'

type CardData = { key: string; name_ar: string; name_en: string; module: string; value: number; format: 'count' | 'money'; route: string }

const ICONS: Record<string, LucideIcon> = {
  properties_offered: ShoppingBag, purchase_requests: Search, rental_requests: KeyRound, total_units: Building, available_units: Home,
  occupied_units: Users, active_contracts: FileSignature, expiring_contracts: AlertTriangle, upcoming_collections: Wallet,
  overdue_rent: AlertTriangle, upcoming_settlements: Landmark, owner_payables: Landmark, maintenance_expenses: Receipt,
  admin_expenses: Receipt, payroll: Users, revenue: TrendingUp, expenses: Receipt, profit: TrendingUp,
}
const TONES: Record<string, string> = {
  overdue_rent: 'from-rose-500 to-pink-600', expiring_contracts: 'from-amber-500 to-orange-600', profit: 'from-emerald-500 to-teal-600',
  revenue: 'from-emerald-500 to-teal-600', owner_payables: 'from-violet-500 to-purple-600', upcoming_settlements: 'from-violet-500 to-purple-600',
}

/** Server-filtered cards: the API returns only cards allowed by modules, permissions and demo settings. */
export function ReDashboardCards() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { formatEGP, formatInteger } = useFormatNumber()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['re-dashboard'],
    queryFn: async () => (await api.get<{ date: string; cards: CardData[] }>('/re-dashboard/cards')).data,
  })
  if (isLoading || isError || !data?.cards.length) return null
  return (
    <section className="mb-6" aria-label={t('re.dashboard.title')}>
      <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('re.dashboard.title')}</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {data.cards.map((c) => {
          const Icon = ICONS[c.key] ?? Home
          return (
            <button key={c.key} type="button" onClick={() => navigate(c.route)}
              className="card stat-card relative flex items-start justify-between pt-7 text-start focus:outline-none focus:ring-2 focus:ring-primary-300">
              <div>
                <p className="text-sm font-medium text-slate-500">{i18n.language === 'ar' ? c.name_ar : c.name_en}</p>
                <p className="mt-2 text-2xl font-bold text-slate-900">{c.format === 'money' ? formatEGP(c.value) : formatInteger(c.value)}</p>
              </div>
              <div className={`rounded-xl bg-gradient-to-br p-3 text-white shadow-lg ${TONES[c.key] ?? 'from-primary-500 to-primary-700'}`}>
                <Icon className="h-6 w-6" />
              </div>
            </button>
          )
        })}
      </div>
    </section>
  )
}
