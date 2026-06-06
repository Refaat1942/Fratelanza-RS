import { Card } from './Card'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string
  icon: LucideIcon
  trend?: string
  color?: string
}

export function StatCard({ title, value, icon: Icon, trend, color = 'bg-primary-50 text-primary-700' }: StatCardProps) {
  return (
    <Card className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
        {trend && <p className="mt-1 text-xs text-emerald-600">{trend}</p>}
      </div>
      <div className={cn('rounded-xl p-3', color)}>
        <Icon className="h-6 w-6" />
      </div>
    </Card>
  )
}
