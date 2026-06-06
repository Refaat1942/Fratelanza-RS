import { ReactNode } from 'react'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const ACCENTS = [
  'from-primary-600 via-primary-500 to-sky-500',
  'from-violet-600 via-purple-500 to-fuchsia-500',
  'from-emerald-600 via-teal-500 to-cyan-500',
  'from-amber-500 via-orange-500 to-rose-500',
  'from-rose-600 via-pink-500 to-violet-500',
  'from-indigo-600 via-blue-500 to-cyan-500',
]

interface PageHeaderProps {
  title: string
  subtitle?: string
  icon?: LucideIcon
  actions?: ReactNode
  accentIndex?: number
  className?: string
}

export function PageHeader({ title, subtitle, icon: Icon, actions, accentIndex = 0, className }: PageHeaderProps) {
  const gradient = ACCENTS[accentIndex % ACCENTS.length]
  return (
    <div className={cn('page-header mb-6 overflow-hidden rounded-2xl shadow-lg shadow-primary-900/5', className)}>
      <div className={cn('relative bg-gradient-to-r px-6 py-5 text-white', gradient)}>
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMtOS45NDEgMC0xOCA4LjA1OS0xOCAxOHM4LjA1OSAxOCAxOCAxOCAxOC04LjA1OSAxOC0xOC04LjA1OS0xOC0xOC0xOHoiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii4wOCIvPjwvZz48L3N2Zz4=')] opacity-40" />
        <div className="relative flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {Icon && (
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm animate-icon-pop">
                <Icon className="h-6 w-6" />
              </div>
            )}
            <div>
              <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
              {subtitle && <p className="mt-0.5 text-sm text-white/85">{subtitle}</p>}
            </div>
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
      </div>
    </div>
  )
}
