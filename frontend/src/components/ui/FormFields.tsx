import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function SelectField({ label, value, onChange, options, required, disabled, placeholder = '—' }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  required?: boolean
  disabled?: boolean
  placeholder?: string
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-slate-700">{label}{required && <span className="text-red-500"> *</span>}</label>
      <select className="input-field" value={value} onChange={(e) => onChange(e.target.value)} required={required} disabled={disabled}>
        <option value="">{placeholder}</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

export function TextAreaField({ label, value, onChange, rows = 3, required }: {
  label: string
  value: string
  onChange: (v: string) => void
  rows?: number
  required?: boolean
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-slate-700">{label}{required && <span className="text-red-500"> *</span>}</label>
      <textarea className="input-field" rows={rows} value={value} onChange={(e) => onChange(e.target.value)} required={required} />
    </div>
  )
}

export function FormGrid({ children }: { children: ReactNode }) {
  return <div className="grid gap-4 sm:grid-cols-2">{children}</div>
}

export function Tabs({ tabs, active, onChange }: {
  tabs: { key: string; label: string }[]
  active: string
  onChange: (key: string) => void
}) {
  return (
    <div className="mb-4 flex gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1 shadow-sm" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          role="tab"
          aria-selected={active === tab.key}
          onClick={() => onChange(tab.key)}
          className={cn(
            'whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            active === tab.key ? 'bg-primary-600 text-white shadow' : 'text-slate-600 hover:bg-slate-100',
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null
  return <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{message}</p>
}

export function SuccessNote({ message }: { message: string | null }) {
  if (!message) return null
  return <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" role="status">{message}</p>
}

export function Badge({ children, tone = 'slate' }: { children: ReactNode; tone?: 'slate' | 'green' | 'amber' | 'red' | 'blue' | 'violet' }) {
  const tones: Record<string, string> = {
    slate: 'bg-slate-100 text-slate-700',
    green: 'bg-emerald-100 text-emerald-800',
    amber: 'bg-amber-100 text-amber-800',
    red: 'bg-red-100 text-red-700',
    blue: 'bg-sky-100 text-sky-800',
    violet: 'bg-violet-100 text-violet-800',
  }
  return <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', tones[tone])}>{children}</span>
}
