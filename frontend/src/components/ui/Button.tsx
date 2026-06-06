import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  loading?: boolean
}

export function Button({ variant = 'primary', loading, className, children, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        variant === 'primary' && 'btn-primary',
        variant === 'secondary' && 'btn-secondary',
        variant === 'ghost' && 'inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100',
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? '...' : children}
    </button>
  )
}
