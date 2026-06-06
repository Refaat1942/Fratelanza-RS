import { Plus, UserPlus, Building2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/stores/authStore'
import { useState } from 'react'
import { ClientFormModal } from '@/components/forms/ClientFormModal'
import { UserFormModal } from '@/components/forms/UserFormModal'
import { CompanyFormModal } from '@/components/forms/CompanyFormModal'

export function QuickActions() {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const [clientOpen, setClientOpen] = useState(false)
  const [userOpen, setUserOpen] = useState(false)
  const [companyOpen, setCompanyOpen] = useState(false)

  return (
    <>
      <div className="flex flex-wrap gap-2 border-b border-slate-200 bg-white px-6 py-3">
        {!user?.is_super_admin && (
          <button
            onClick={() => setClientOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-700 px-3 py-2 text-sm font-medium text-white hover:bg-primary-800"
          >
            <UserPlus className="h-4 w-4" />
            {t('add_client')}
          </button>
        )}
        {user?.is_super_admin ? (
          <button
            onClick={() => setCompanyOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-700 px-3 py-2 text-sm font-medium text-white hover:bg-primary-800"
          >
            <Building2 className="h-4 w-4" />
            {t('add_company')}
          </button>
        ) : (
          <button
            onClick={() => setUserOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <Plus className="h-4 w-4" />
            {t('add_user')}
          </button>
        )}
      </div>
      <ClientFormModal open={clientOpen} onClose={() => setClientOpen(false)} />
      <UserFormModal open={userOpen} onClose={() => setUserOpen(false)} />
      <CompanyFormModal open={companyOpen} onClose={() => setCompanyOpen(false)} />
    </>
  )
}
