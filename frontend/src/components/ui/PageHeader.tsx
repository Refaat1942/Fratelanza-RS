import { ReactNode } from 'react'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const ACCENTS = [
  'from-primary-800 via-primary-700 to-primary-600',
  'from-violet-800 via-purple-700 to-fuchsia-700',
  'from-emerald-800 via-teal-700 to-cyan-700',
  'from-amber-700 via-orange-700 to-rose-700',
  'from-rose-800 via-pink-700 to-violet-700',
  'from-indigo-800 via-blue-700 to-cyan-700',
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
    <div className={cn('page-header mb-6 overflow-hidden rounded-2xl shadow-lg shadow-primary-900/10', className)}>
      <div className={cn('relative bg-gradient-to-r px-6 py-5 text-white', gradient)}>
        <div className="absolute inset-0 bg-black/15" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMtOS45NDEgMC0xOCA4LjA1OS0xOCAxOHM4LjA1OSAxOCAxOCAxOCAxOC04LjA1OSAxOC0xOC04LjA1OS0xOC0xOC0xOHoiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii4wNSIvPjwvZz48L3N2Zz4=')] opacity-30" />
        <div className="relative flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {Icon && (
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm animate-icon-pop">
                <Icon className="h-6 w-6 text-white" />
              </div>
            )}
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white [text-shadow:0_1px_2px_rgba(0,0,0,0.25)]">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-0.5 text-sm font-medium text-white/95 [text-shadow:0_1px_2px_rgba(0,0,0,0.2)]">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {actions && (
            <div className="flex flex-wrap items-center gap-2 [&_.btn-secondary]:border-white/30 [&_.btn-secondary]:bg-white [&_.btn-secondary]:text-slate-800 [&_.btn-secondary]:shadow-md">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
