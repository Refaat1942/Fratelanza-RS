import { Outlet } from 'react-router-dom'
import { AnimatedPage } from '@/components/ui/AnimatedPage'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { QuickActions } from './QuickActions'
import { TrialBanner } from './TrialBanner'

export function DashboardLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <TrialBanner />
        <QuickActions />
        <main className="main-canvas">
          <AnimatedPage>
            <Outlet />
          </AnimatedPage>
        </main>
      </div>
    </div>
  )
}
