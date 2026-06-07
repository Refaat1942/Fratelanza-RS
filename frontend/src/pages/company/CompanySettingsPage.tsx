import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Settings, Users, Shield, Sliders, Plus, UserCog, KeyRound, Ban, CheckCircle,
} from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { DataTable } from '@/components/ui/DataTable'
import { LoadingState } from '@/components/ui/LoadingState'
import { UserFormModal } from '@/components/forms/UserFormModal'
import { UserEditModal } from '@/components/forms/UserEditModal'
import { UserFeaturesModal } from '@/components/forms/UserFeaturesModal'
import { ResetPasswordModal } from '@/components/forms/ResetPasswordModal'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { useListData } from '@/hooks/useListData'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type SettingsTab = 'users' | 'authorization' | 'features'

const ROLE_PERMISSIONS: { role: string; permissions: string[] }[] = [
  { role: 'company_admin', permissions: ['users', 'settings', 'all_modules'] },
  { role: 'sales_manager', permissions: ['customers', 'leads', 'reservations', 'contracts', 'reports'] },
  { role: 'sales_agent', permissions: ['customers', 'leads', 'reservations', 'follow_ups'] },
  { role: 'collection_officer', permissions: ['collections', 'contracts', 'customers', 'reports'] },
  { role: 'accountant', permissions: ['finance', 'collections', 'reports'] },
  { role: 'customer_service', permissions: ['customers', 'tickets', 'follow_ups'] },
  { role: 'hr_officer', permissions: ['hr', 'reports'] },
]

export function CompanySettingsPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [tab, setTab] = useState<SettingsTab>('users')
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<Record<string, unknown> | null>(null)
  const [featuresUser, setFeaturesUser] = useState<Record<string, unknown> | null>(null)
  const [resetUser, setResetUser] = useState<Record<string, unknown> | null>(null)

  const deleteUser = useDeleteEntity('/users', ['company-users'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('company-users', '/users')
  const rows = Array.isArray(items) ? items : []

  const { data: modulesData, isLoading: modulesLoading } = useQuery({
    queryKey: ['company-modules-me'],
    queryFn: async () => {
      const { data: res } = await api.get<{
        enabled: string[]
        catalog: { key: string; name_en: string; name_ar: string; core: boolean }[]
      }>('/modules/company/me')
      return res
    },
    enabled: tab === 'features',
  })

  const toggleStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const endpoint = status === 'active' ? 'suspend' : 'activate'
      return api.post(`/users/${id}/${endpoint}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['company-users'] })
      refetch()
    },
  })

  const tabs: { key: SettingsTab; label: string; icon: typeof Users }[] = [
    { key: 'users', label: t('settings_tab_users'), icon: Users },
    { key: 'authorization', label: t('settings_tab_authorization'), icon: Shield },
    { key: 'features', label: t('settings_tab_features'), icon: Sliders },
  ]

  const enabledSet = new Set(modulesData?.enabled ?? [])

  return (
    <div>
      <PageHeader
        title={t('settings')}
        subtitle={t('company_settings_subtitle')}
        icon={Settings}
        accentIndex={3}
      />

      <div className="mb-6 flex flex-wrap gap-2 border-b border-slate-200 pb-1">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={cn(
              'inline-flex items-center gap-2 rounded-t-lg px-4 py-2.5 text-sm font-medium transition',
              tab === key
                ? 'border-b-2 border-primary-600 text-primary-700'
                : 'text-slate-500 hover:text-slate-700',
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'users' && (
        <div>
          <DataTable
            title={t('users')}
            subtitle={t('settings_users_help')}
            loading={isLoading}
            exportFilename="users"
            data={rows}
            columns={[
              { key: 'username', label: t('username') },
              { key: 'full_name_ar', label: t('name_ar') },
              { key: 'email', label: t('email') },
              { key: 'system_role', label: t('role'), render: (row) => String(row.system_role).replace(/_/g, ' ') },
              {
                key: 'status',
                label: t('status'),
                render: (row) => (
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    row.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700',
                  )}>
                    {String(row.status)}
                  </span>
                ),
              },
            ]}
            actions={
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="me-2 h-4 w-4" />
                {t('add_user')}
              </Button>
            }
            rowActions={(row) => (
              <div className="flex flex-wrap items-center gap-1">
                <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => setEditUser(row)} title={t('edit')}>
                  <UserCog className="h-4 w-4 text-primary-600" />
                </Button>
                <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => setFeaturesUser(row)} title={t('user_feature_access')}>
                  <Sliders className="h-4 w-4 text-primary-600" />
                </Button>
                <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => setResetUser(row)} title={t('reset_password')}>
                  <KeyRound className="h-4 w-4 text-amber-600" />
                </Button>
                {row.status === 'active' ? (
                  <Button
                    variant="ghost"
                    className="!px-2 !py-1.5"
                    onClick={() => toggleStatus.mutate({ id: row.id as number, status: 'active' })}
                    title={t('suspend_user')}
                  >
                    <Ban className="h-4 w-4 text-red-600" />
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    className="!px-2 !py-1.5"
                    onClick={() => toggleStatus.mutate({ id: row.id as number, status: 'suspended' })}
                    title={t('activate_user')}
                  >
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  className="!px-2 !py-1.5 text-red-600"
                  onClick={() => confirmDelete(t) && deleteUser.mutate(row.id as number, { onSuccess: () => refetch() })}
                  title={t('delete')}
                >
                  {t('delete')}
                </Button>
              </div>
            )}
          />
          <UserFormModal open={createOpen} onClose={() => { setCreateOpen(false); refetch() }} />
          <UserEditModal
            open={!!editUser}
            user={editUser as Parameters<typeof UserEditModal>[0]['user']}
            onClose={() => setEditUser(null)}
            onSaved={() => refetch()}
          />
          <UserFeaturesModal
            open={!!featuresUser}
            userId={featuresUser?.id as number}
            userName={String(i18n.language === 'ar' ? featuresUser?.full_name_ar : featuresUser?.full_name_en ?? '')}
            onClose={() => setFeaturesUser(null)}
            onSaved={() => refetch()}
          />
          <ResetPasswordModal
            open={!!resetUser}
            userId={resetUser?.id as number}
            userEmail={String(resetUser?.email ?? '')}
            onClose={() => setResetUser(null)}
          />
        </div>
      )}

      {tab === 'authorization' && (
        <div>
          <Card className="mb-6 border-blue-200 bg-blue-50/50">
            <div className="flex items-start gap-3">
              <Shield className="mt-0.5 h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900">{t('authorization_overview')}</p>
                <p className="mt-1 text-sm text-blue-800">{t('authorization_overview_help')}</p>
              </div>
            </div>
          </Card>
          <div className="space-y-4">
            {ROLE_PERMISSIONS.map(({ role, permissions }) => (
              <div key={role} className="rounded-xl border border-slate-200 bg-white p-4">
                <h3 className="font-semibold capitalize text-slate-900">{role.replace(/_/g, ' ')}</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {permissions.map((perm) => (
                    <span key={perm} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                      {perm.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="mt-6 text-sm text-slate-600">{t('per_user_features_hint')}</p>
        </div>
      )}

      {tab === 'features' && (
        <div>
          <Card className="mb-6 border-blue-200 bg-blue-50/50">
            <div className="flex items-start gap-3">
              <Shield className="mt-0.5 h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900">{t('company_features_note')}</p>
                <p className="mt-1 text-sm text-blue-800">{t('company_features_contact_superadmin')}</p>
              </div>
            </div>
          </Card>
          {modulesLoading ? (
            <LoadingState />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {(modulesData?.catalog ?? []).map((mod) => {
                const on = enabledSet.has(mod.key)
                const name = i18n.language === 'ar' ? mod.name_ar : mod.name_en
                return (
                  <div
                    key={mod.key}
                    className={cn(
                      'rounded-lg border px-4 py-3 text-sm',
                      on ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-slate-200 bg-slate-50 text-slate-500',
                    )}
                  >
                    <span className="font-medium">{name}</span>
                    {mod.core && <span className="ms-2 text-xs opacity-70">({t('required')})</span>}
                    <span className="mt-1 block text-xs">{on ? t('enabled') : t('disabled')}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
