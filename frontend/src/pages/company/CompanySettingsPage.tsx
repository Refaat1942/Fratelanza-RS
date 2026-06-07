import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { KeyRound, Settings, ShieldCheck, Sliders, Users } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { UserAdministrationPanel } from '@/components/settings/UserAdministrationPanel'
import { ChangePasswordModal } from '@/components/forms/ChangePasswordModal'
import { CompanyFeatureSettingsPage } from '@/pages/company/CompanyFeatureSettingsPage'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'
import { formatRole } from '@/lib/userRoles'

type SettingsTab = 'users' | 'features' | 'security'

const tabs: { id: SettingsTab; label: string; icon: typeof Users }[] = [
  { id: 'users', label: 'users_and_authorizations', icon: Users },
  { id: 'features', label: 'feature_settings', icon: Sliders },
  { id: 'security', label: 'security', icon: ShieldCheck },
]

export function CompanySettingsPage() {
  const { t, i18n } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const [activeTab, setActiveTab] = useState<SettingsTab>('users')
  const [passwordOpen, setPasswordOpen] = useState(false)

  const displayName = user
    ? (i18n.language === 'ar' ? user.full_name_ar || user.full_name_en : user.full_name_en || user.full_name_ar)
    : ''

  return (
    <div>
      <PageHeader
        title={t('settings')}
        subtitle={t('company_settings_help')}
        icon={Settings}
        accentIndex={3}
      />

      <Card className="mb-6 p-2">
        <div className="flex flex-wrap gap-2">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={cn(
                'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition',
                activeTab === id
                  ? 'bg-primary-700 text-white shadow-md'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              )}
            >
              <Icon className="h-4 w-4" />
              {t(label)}
            </button>
          ))}
        </div>
      </Card>

      {activeTab === 'users' && (
        <UserAdministrationPanel
          title={t('users_and_authorizations')}
          subtitle={t('company_users_admin_help')}
        />
      )}

      {activeTab === 'features' && <CompanyFeatureSettingsPage embedded />}

      {activeTab === 'security' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <div className="mb-4 flex items-start gap-3">
              <div className="rounded-lg bg-primary-50 p-2 text-primary-700">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{t('account_security')}</h2>
                <p className="text-sm text-slate-500">{t('account_security_help')}</p>
              </div>
            </div>
            <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">{t('user')}</span>
                <span className="font-medium text-slate-900">{displayName}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">{t('role')}</span>
                <span className="font-medium capitalize text-slate-900">{formatRole(user?.system_role)}</span>
              </div>
            </div>
            <Button className="mt-4" onClick={() => setPasswordOpen(true)}>
              <KeyRound className="me-2 h-4 w-4" />
              {t('change_password')}
            </Button>
          </Card>

          <Card className="border-blue-200 bg-blue-50/60">
            <h2 className="text-lg font-semibold text-blue-950">{t('authorization_model')}</h2>
            <p className="mt-2 text-sm text-blue-900">{t('authorization_model_help')}</p>
          </Card>
        </div>
      )}

      <ChangePasswordModal open={passwordOpen} onClose={() => setPasswordOpen(false)} />
    </div>
  )
}
