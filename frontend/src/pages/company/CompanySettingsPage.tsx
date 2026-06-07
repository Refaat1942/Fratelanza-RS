import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { KeyRound, Power, Settings, Shield, Sliders, Users } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { CompanyUsersPage } from '@/pages/company/ModulePages'
import { CompanyFeatureSettingsPage } from '@/pages/company/CompanyFeatureSettingsPage'
import { UserFeaturesModal } from '@/components/forms/UserFeaturesModal'
import api from '@/lib/api'
import { cn } from '@/lib/utils'
import { roleLabel } from '@/constants/roles'
import type { Paginated } from '@/types'
import type { ModuleCatalogItem } from '@/stores/modulesStore'

type SettingsTab = 'users' | 'authorizations' | 'features'

interface SettingsUser {
  id: number
  username?: string
  email: string
  full_name_ar: string
  full_name_en: string
  system_role: string
  status: string
  is_super_admin: boolean
}

interface CompanyModulesResponse {
  enabled: string[]
  catalog: ModuleCatalogItem[]
}

export function CompanySettingsPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [tab, setTab] = useState<SettingsTab>('users')
  const [featuresUser, setFeaturesUser] = useState<SettingsUser | null>(null)

  const usersQuery = useQuery({
    queryKey: ['settings-users'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<SettingsUser>>('/users', { params: { page_size: 100 } })
      return data
    },
  })

  const modulesQuery = useQuery({
    queryKey: ['settings-company-modules'],
    queryFn: async () => {
      const { data } = await api.get<CompanyModulesResponse>('/modules/company/me')
      return data
    },
  })

  const users = usersQuery.data?.items ?? []
  const enabledModules = new Set(modulesQuery.data?.enabled ?? [])
  const enabledCatalog = (modulesQuery.data?.catalog ?? []).filter((mod) => enabledModules.has(mod.key))

  const roleStats = useMemo(() => {
    const map = new Map<string, number>()
    for (const user of users) {
      map.set(user.system_role, (map.get(user.system_role) ?? 0) + 1)
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [users])

  const tabs = [
    { key: 'users' as const, label: t('settings_users_tab'), icon: Users },
    { key: 'authorizations' as const, label: t('settings_authorizations_tab'), icon: Shield },
    { key: 'features' as const, label: t('settings_features_tab'), icon: Sliders },
  ]

  return (
    <div>
      <PageHeader
        title={t('settings')}
        subtitle={t('company_settings_help')}
        icon={Settings}
        accentIndex={3}
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={cn(
              'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium',
              tab === key
                ? 'bg-primary-700 text-white shadow-sm'
                : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50',
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'users' && <CompanyUsersPage />}

      {tab === 'authorizations' && (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-primary-50 p-2 text-primary-700"><Users className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t('total_users')}</p>
                <p className="text-xl font-bold">{users.length}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-emerald-50 p-2 text-emerald-700"><Power className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t('active_users')}</p>
                <p className="text-xl font-bold">{users.filter((user) => user.status === 'active').length}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-amber-50 p-2 text-amber-700"><Sliders className="h-5 w-5" /></div>
              <div>
                <p className="text-xs text-slate-500">{t('enabled_features')}</p>
                <p className="text-xl font-bold">{enabledCatalog.length}</p>
              </div>
            </Card>
          </div>

          <Card>
            <div className="mb-4 flex items-start gap-3">
              <Shield className="mt-1 h-5 w-5 text-primary-700" />
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{t('authorization_model')}</h2>
                <p className="mt-1 text-sm text-slate-500">{t('authorization_model_help')}</p>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-medium text-slate-900">{t('role')}</p>
                <p className="mt-1 text-sm text-slate-500">{t('role_authorization_help')}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-medium text-slate-900">{t('features')}</p>
                <p className="mt-1 text-sm text-slate-500">{t('feature_authorization_help')}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-medium text-slate-900">{t('account_security')}</p>
                <p className="mt-1 text-sm text-slate-500">{t('account_security_help')}</p>
              </div>
            </div>
          </Card>

          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <h2 className="mb-3 text-lg font-semibold text-slate-900">{t('roles_summary')}</h2>
              {usersQuery.isLoading ? (
                <LoadingState />
              ) : roleStats.length === 0 ? (
                <EmptyState title={t('no_data')} description={t('no_data_help')} />
              ) : (
                <div className="space-y-2">
                  {roleStats.map(([role, count]) => (
                    <div key={role} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                      <span className="text-sm font-medium capitalize text-slate-700">{roleLabel(role)}</span>
                      <span className="rounded-full bg-primary-50 px-2 py-0.5 text-xs font-semibold text-primary-700">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card className="lg:col-span-2">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">{t('per_user_authorizations')}</h2>
                  <p className="text-sm text-slate-500">{t('per_user_authorizations_help')}</p>
                </div>
                <KeyRound className="h-5 w-5 text-slate-400" />
              </div>
              {usersQuery.isLoading || modulesQuery.isLoading ? (
                <LoadingState />
              ) : users.length === 0 ? (
                <EmptyState title={t('no_data')} description={t('no_data_help')} />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="table-head-gradient">
                        <th className="px-3 py-3 text-start">{t('user')}</th>
                        <th className="px-3 py-3 text-start">{t('role')}</th>
                        <th className="px-3 py-3 text-start">{t('status')}</th>
                        <th className="px-3 py-3 text-start">{t('actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => {
                        const name = i18n.language === 'ar' ? user.full_name_ar : user.full_name_en
                        return (
                          <tr key={user.id} className="border-b border-slate-100">
                            <td className="px-3 py-3">
                              <p className="font-medium text-slate-900">{name}</p>
                              <p className="text-xs text-slate-500">{user.username || user.email}</p>
                            </td>
                            <td className="px-3 py-3 capitalize">{roleLabel(user.system_role)}</td>
                            <td className="px-3 py-3">{t(user.status)}</td>
                            <td className="px-3 py-3">
                              <Button variant="secondary" onClick={() => setFeaturesUser(user)}>
                                <Sliders className="me-2 h-4 w-4" />
                                {t('user_feature_access')}
                              </Button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {tab === 'features' && <CompanyFeatureSettingsPage />}

      <UserFeaturesModal
        open={!!featuresUser}
        userId={featuresUser?.id ?? 0}
        userName={featuresUser ? String((i18n.language === 'ar' ? featuresUser.full_name_ar : featuresUser.full_name_en) ?? '') : ''}
        onClose={() => setFeaturesUser(null)}
        onSaved={() => {
          qc.invalidateQueries({ queryKey: ['settings-users'] })
          setFeaturesUser(null)
        }}
      />
    </div>
  )
}
