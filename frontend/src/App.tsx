import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { SuperAdminDashboard } from '@/pages/super-admin/SuperAdminDashboard'
import { CompaniesPage } from '@/pages/super-admin/CompaniesPage'
import { SuperAdminUsersPage } from '@/pages/super-admin/SuperAdminUsersPage'
import { CompanyDashboard } from '@/pages/company/CompanyDashboard'
import { CustomersPage } from '@/pages/company/CustomersPage'
import { LeadsPage } from '@/pages/company/LeadsPage'
import { AIAssistantPage } from '@/pages/company/AIAssistantPage'
import {
  ProjectsPage, ReservationsPage, ContractsPage, CollectionsPage,
  BrokersPage, FinancePage, ConstructionPage, ProcurementPage,
  WarehousePage, PropertyPage, CustomerServicePage, CompanyUsersPage,
  AuditLogsPage, SubscriptionsPage, SettingsPage,
} from '@/pages/company/ModulePages'

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
      <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route path="/super-admin" element={<ProtectedRoute superAdminOnly><SuperAdminDashboard /></ProtectedRoute>} />
        <Route path="/super-admin/companies" element={<ProtectedRoute superAdminOnly><CompaniesPage /></ProtectedRoute>} />
        <Route path="/super-admin/users" element={<ProtectedRoute superAdminOnly><SuperAdminUsersPage /></ProtectedRoute>} />
        <Route path="/super-admin/subscriptions" element={<ProtectedRoute superAdminOnly><SubscriptionsPage /></ProtectedRoute>} />
        <Route path="/super-admin/audit-logs" element={<ProtectedRoute superAdminOnly><AuditLogsPage /></ProtectedRoute>} />
        <Route path="/super-admin/settings" element={<ProtectedRoute superAdminOnly><SettingsPage /></ProtectedRoute>} />
        <Route path="/dashboard" element={<CompanyDashboard />} />
        <Route path="/customers" element={<CustomersPage />} />
        <Route path="/leads" element={<LeadsPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/reservations" element={<ReservationsPage />} />
        <Route path="/contracts" element={<ContractsPage />} />
        <Route path="/collections" element={<CollectionsPage />} />
        <Route path="/brokers" element={<BrokersPage />} />
        <Route path="/finance" element={<FinancePage />} />
        <Route path="/construction" element={<ConstructionPage />} />
        <Route path="/procurement" element={<ProcurementPage />} />
        <Route path="/warehouse" element={<WarehousePage />} />
        <Route path="/property" element={<PropertyPage />} />
        <Route path="/customer-service" element={<CustomerServicePage />} />
        <Route path="/users" element={<CompanyUsersPage />} />
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
