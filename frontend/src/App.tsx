import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { SuperAdminDashboard } from '@/pages/super-admin/SuperAdminDashboard'
import { CompaniesPage } from '@/pages/super-admin/CompaniesPage'
import { CompanyDashboard } from '@/pages/company/CompanyDashboard'
import { CustomersPage } from '@/pages/company/CustomersPage'
import { LeadsPage } from '@/pages/company/LeadsPage'
import { PlaceholderPage } from '@/pages/company/PlaceholderPage'
import { AIAssistantPage } from '@/pages/company/AIAssistantPage'

function ProtectedRoute({ children, superAdminOnly = false }: { children: React.ReactNode; superAdminOnly?: boolean }) {
  const user = useAuthStore((s) => s.user)
  const accessToken = useAuthStore((s) => s.accessToken)
  if (!accessToken || !user) return <Navigate to="/login" replace />
  if (superAdminOnly && !user.is_super_admin) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function AppRoutes() {
  const user = useAuthStore((s) => s.user)
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={user.is_super_admin ? '/super-admin' : '/dashboard'} /> : <LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/super-admin" element={<ProtectedRoute superAdminOnly><SuperAdminDashboard /></ProtectedRoute>} />
        <Route path="/super-admin/companies" element={<ProtectedRoute superAdminOnly><CompaniesPage /></ProtectedRoute>} />
        <Route path="/super-admin/users" element={<ProtectedRoute superAdminOnly><PlaceholderPage titleKey="users" /></ProtectedRoute>} />
        <Route path="/super-admin/subscriptions" element={<ProtectedRoute superAdminOnly><PlaceholderPage titleKey="subscriptions" /></ProtectedRoute>} />
        <Route path="/super-admin/audit-logs" element={<ProtectedRoute superAdminOnly><PlaceholderPage titleKey="audit_logs" /></ProtectedRoute>} />
        <Route path="/super-admin/settings" element={<ProtectedRoute superAdminOnly><PlaceholderPage titleKey="settings" /></ProtectedRoute>} />
        <Route path="/dashboard" element={<CompanyDashboard />} />
        <Route path="/customers" element={<CustomersPage />} />
        <Route path="/leads" element={<LeadsPage />} />
        <Route path="/projects" element={<PlaceholderPage titleKey="projects" />} />
        <Route path="/reservations" element={<PlaceholderPage titleKey="reservations" />} />
        <Route path="/contracts" element={<PlaceholderPage titleKey="contracts" />} />
        <Route path="/collections" element={<PlaceholderPage titleKey="collections" />} />
        <Route path="/brokers" element={<PlaceholderPage titleKey="brokers" />} />
        <Route path="/finance" element={<PlaceholderPage titleKey="finance" />} />
        <Route path="/construction" element={<PlaceholderPage titleKey="construction" />} />
        <Route path="/procurement" element={<PlaceholderPage titleKey="procurement" />} />
        <Route path="/warehouse" element={<PlaceholderPage titleKey="warehouse" />} />
        <Route path="/property" element={<PlaceholderPage titleKey="property" />} />
        <Route path="/customer-service" element={<PlaceholderPage titleKey="customer_service" />} />
        <Route path="/ai-assistant" element={<AIAssistantPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default function App() {
  const { i18n } = useTranslation()

  useEffect(() => {
    const lang = localStorage.getItem('language') || 'ar'
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    i18n.changeLanguage(lang)
  }, [i18n])

  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
