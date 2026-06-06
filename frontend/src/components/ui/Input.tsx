import { cn } from '@/lib/utils'
import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && <label className="block text-sm font-medium text-slate-700">{label}</label>}
      <input ref={ref} className={cn('input-field', error && 'border-red-500', className)} {...props} />
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  ),
)
Input.displayName = 'Input'
