import { Plus, UserPlus, Building2, Phone, Users } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useState } from 'react'
import { ClientFormModal } from '@/components/forms/ClientFormModal'
import { UserFormModal } from '@/components/forms/UserFormModal'
import { CompanyFormModal } from '@/components/forms/CompanyFormModal'
import { ReminderFormModal } from '@/components/forms/ReminderFormModal'
import { useModulesStore } from '@/stores/modulesStore'

export function QuickActions() {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const location = useLocation()
  const { isEnabled } = useModulesStore()
  const [clientOpen, setClientOpen] = useState(false)
  const [userOpen, setUserOpen] = useState(false)
  const [companyOpen, setCompanyOpen] = useState(false)
  const [reminderOpen, setReminderOpen] = useState(false)

  if (user?.is_super_admin) {
    if (!location.pathname.startsWith('/super-admin/companies')) {
      return null
    }
    return (
      <>
        <div className="quick-actions-bar">
          <button onClick={() => setCompanyOpen(true)} className="btn-primary gap-2 px-3 py-2 text-sm">
            <Building2 className="h-4 w-4" />{t('add_company')}
          </button>
        </div>
        <CompanyFormModal open={companyOpen} onClose={() => setCompanyOpen(false)} />
      </>
    )
  }

  return (
    <>
      <div className="quick-actions-bar">
        {isEnabled('customers') && (
          <button onClick={() => setClientOpen(true)} className="btn-primary gap-2 px-3 py-2 text-sm">
            <UserPlus className="h-4 w-4" />{t('add_client')}
          </button>
        )}
        {isEnabled('follow_ups') && (
          <button onClick={() => setReminderOpen(true)} className="inline-flex items-center gap-2 rounded-lg border border-primary-200 bg-primary-50 px-3 py-2 text-sm font-medium text-primary-800 hover:bg-primary-100">
            <Phone className="h-4 w-4" />{t('schedule_call')}
          </button>
        )}
        {isEnabled('users') && (
          <button onClick={() => setUserOpen(true)} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
            <Plus className="h-4 w-4" />{t('add_user')}
          </button>
        )}
        {isEnabled('hr') && (
          <Link to="/hr" className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
            <Users className="h-4 w-4" />{t('add_employee')}
          </Link>
        )}
      </div>
      <ClientFormModal open={clientOpen} onClose={() => setClientOpen(false)} />
      <UserFormModal open={userOpen} onClose={() => setUserOpen(false)} />
      <ReminderFormModal open={reminderOpen} onClose={() => setReminderOpen(false)} />
    </>
  )
}
