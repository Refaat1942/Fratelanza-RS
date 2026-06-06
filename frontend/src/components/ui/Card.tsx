import { cn } from '@/lib/utils'
import { ReactNode } from 'react'

export function Card({ children, className, gradient }: { children: ReactNode; className?: string; gradient?: boolean }) {
  return (
    <div className={cn('card', gradient && 'card-gradient-border', className)}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-lg font-semibold text-gradient">{title}</h3>
      {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
    </div>
  )
}
