import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { ModuleRoute } from '@/components/auth/ModuleRoute'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { SuperAdminDashboard } from '@/pages/super-admin/SuperAdminDashboard'
import { CompaniesPage } from '@/pages/super-admin/CompaniesPage'
import { SuperAdminUsersPage } from '@/pages/super-admin/SuperAdminUsersPage'
import { SubscriptionPlansPage } from '@/pages/super-admin/SubscriptionPlansPage'
import { SuperAdminSettingsPage } from '@/pages/super-admin/SuperAdminSettingsPage'
import { CompanyDashboard } from '@/pages/company/CompanyDashboard'
import { CustomersPage } from '@/pages/company/CustomersPage'
import { LeadsPage } from '@/pages/company/LeadsPage'
import { AIAssistantPage } from '@/pages/company/AIAssistantPage'
import { ReportsPage } from '@/pages/company/ReportsPage'
import { HRPage } from '@/pages/company/HRPage'
import { FinancePage } from '@/pages/company/FinancePage'
import { FollowUpsPage } from '@/pages/company/FollowUpsPage'
import { BrandingPage } from '@/pages/company/BrandingPage'
import { CompanyFeatureSettingsPage } from '@/pages/company/CompanyFeatureSettingsPage'
import { ProjectsPage } from '@/pages/company/ProjectsPage'
import { WarehousePage } from '@/pages/company/WarehousePage'
import { DocumentsPage } from '@/pages/company/DocumentsPage'
import { PropertyPage } from '@/pages/company/PropertyPage'
import {
  ReservationsPage, ContractsPage, CollectionsPage,
  BrokersPage, ConstructionPage, ProcurementPage,
  CustomerServicePage, CompanyUsersPage,
  AuditLogsPage,
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
        <Route path="/super-admin/subscriptions" element={<ProtectedRoute superAdminOnly><SubscriptionPlansPage /></ProtectedRoute>} />
        <Route path="/super-admin/audit-logs" element={<ProtectedRoute superAdminOnly><AuditLogsPage /></ProtectedRoute>} />
        <Route path="/super-admin/settings" element={<ProtectedRoute superAdminOnly><SuperAdminSettingsPage /></ProtectedRoute>} />
        <Route path="/super-admin/reports" element={<ProtectedRoute superAdminOnly><ReportsPage /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ModuleRoute moduleKey="dashboard"><CompanyDashboard /></ModuleRoute>} />
        <Route path="/customers" element={<ModuleRoute moduleKey="customers"><CustomersPage /></ModuleRoute>} />
        <Route path="/leads" element={<ModuleRoute moduleKey="leads"><LeadsPage /></ModuleRoute>} />
        <Route path="/projects" element={<ModuleRoute moduleKey="projects"><ProjectsPage /></ModuleRoute>} />
        <Route path="/reservations" element={<ModuleRoute moduleKey="reservations"><ReservationsPage /></ModuleRoute>} />
        <Route path="/contracts" element={<ModuleRoute moduleKey="contracts"><ContractsPage /></ModuleRoute>} />
        <Route path="/collections" element={<ModuleRoute moduleKey="collections"><CollectionsPage /></ModuleRoute>} />
        <Route path="/brokers" element={<ModuleRoute moduleKey="brokers"><BrokersPage /></ModuleRoute>} />
        <Route path="/finance" element={<ModuleRoute moduleKey="finance"><FinancePage /></ModuleRoute>} />
        <Route path="/hr" element={<ModuleRoute moduleKey="hr"><HRPage /></ModuleRoute>} />
        <Route path="/follow-ups" element={<ModuleRoute moduleKey="follow_ups"><FollowUpsPage /></ModuleRoute>} />
        <Route path="/branding" element={<ModuleRoute moduleKey="branding"><BrandingPage /></ModuleRoute>} />
        <Route path="/construction" element={<ModuleRoute moduleKey="construction"><ConstructionPage /></ModuleRoute>} />
        <Route path="/procurement" element={<ModuleRoute moduleKey="procurement"><ProcurementPage /></ModuleRoute>} />
        <Route path="/warehouse" element={<ModuleRoute moduleKey="warehouse"><WarehousePage /></ModuleRoute>} />
        <Route path="/documents" element={<ModuleRoute moduleKey="documents"><DocumentsPage /></ModuleRoute>} />
        <Route path="/property" element={<ModuleRoute moduleKey="property"><PropertyPage /></ModuleRoute>} />
        <Route path="/customer-service" element={<ModuleRoute moduleKey="customer_service"><CustomerServicePage /></ModuleRoute>} />
        <Route path="/users" element={<ModuleRoute moduleKey="users"><CompanyUsersPage /></ModuleRoute>} />
        <Route path="/feature-settings" element={<ModuleRoute moduleKey="users"><CompanyFeatureSettingsPage /></ModuleRoute>} />
        <Route path="/reports" element={<ModuleRoute moduleKey="reports"><ReportsPage /></ModuleRoute>} />
        <Route path="/ai-assistant" element={<ModuleRoute moduleKey="ai_assistant"><AIAssistantPage /></ModuleRoute>} />
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
