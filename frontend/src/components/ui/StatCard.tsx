import { Card } from './Card'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const ICON_GRADIENTS: Record<string, string> = {
  default: 'bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-lg shadow-primary-500/30',
  emerald: 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/30',
  amber: 'bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/30',
  violet: 'bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/30',
  rose: 'bg-gradient-to-br from-rose-500 to-pink-600 text-white shadow-lg shadow-rose-500/30',
  sky: 'bg-gradient-to-br from-sky-500 to-cyan-600 text-white shadow-lg shadow-sky-500/30',
}

function gradientKey(color?: string): string {
  if (!color) return 'default'
  if (color.includes('emerald')) return 'emerald'
  if (color.includes('amber')) return 'amber'
  if (color.includes('violet')) return 'violet'
  if (color.includes('rose')) return 'rose'
  if (color.includes('sky')) return 'sky'
  return 'default'
}

interface StatCardProps {
  title: string
  value: string
  icon: LucideIcon
  trend?: string
  color?: string
}

export function StatCard({ title, value, icon: Icon, trend, color }: StatCardProps) {
  const iconClass = ICON_GRADIENTS[gradientKey(color)]
  return (
    <Card className="stat-card relative flex items-start justify-between pt-7">
      <div>
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <p className="mt-2 text-2xl font-bold text-slate-900 transition-all duration-300">{value}</p>
        {trend && <p className="mt-1 text-xs font-medium text-emerald-600">{trend}</p>}
      </div>
      <div className={cn('rounded-xl p-3 transition-transform duration-300 hover:scale-110', iconClass)}>
        <Icon className="h-6 w-6" />
      </div>
    </Card>
  )
}
