import { ReactNode } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  className?: string
}

export function Modal({ open, onClose, title, children, className }: ModalProps) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="modal-backdrop" onClick={onClose} />
      <div className={cn(
        'modal-panel relative z-10 w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl shadow-primary-900/20',
        className,
      )}>
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-primary-50 to-violet-50 px-6 py-4">
          <h2 className="text-lg font-semibold text-gradient">{title}</h2>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white hover:text-slate-700 hover:shadow-sm">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto p-6">{children}</div>
      </div>
    </div>
  )
}
