import { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'

export function AnimatedPage({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  return (
    <div key={pathname} className="page-enter relative">
      <div className="pointer-events-none absolute -end-20 -top-20 h-64 w-64 rounded-full bg-primary-400/10 blur-3xl animate-float-slow" />
      <div className="pointer-events-none absolute bottom-10 start-10 h-48 w-48 rounded-full bg-sky-400/10 blur-3xl animate-float-slower" />
      <div className="pointer-events-none absolute end-1/4 top-1/3 h-32 w-32 rounded-full bg-violet-400/10 blur-2xl animate-pulse-soft" />
      <div className="relative z-10">{children}</div>
    </div>
  )
}
