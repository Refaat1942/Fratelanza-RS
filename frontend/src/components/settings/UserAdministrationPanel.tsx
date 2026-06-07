import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { KeyRound, Plus, ShieldCheck, Sliders, UserCheck, UserX, Users } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { DataTable } from '@/components/ui/DataTable'
import { Button } from '@/components/ui/Button'
import { RowActions } from '@/components/ui/RowActions'
import { UserFormModal } from '@/components/forms/UserFormModal'
import { UserEditModal } from '@/components/forms/UserEditModal'
import { UserFeaturesModal } from '@/components/forms/UserFeaturesModal'
import { ResetPasswordModal } from '@/components/forms/ResetPasswordModal'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { useAuthStore } from '@/stores/authStore'
import { formatRole } from '@/lib/userRoles'
import api from '@/lib/api'
import type { Paginated } from '@/types'

interface CompanyUser {
  id: number
  username?: string
  email: string
  full_name_ar: string
  full_name_en: string
  phone?: string
  system_role: string
  status: string
  company_id?: number
  is_super_admin: boolean
}

interface UserAdministrationPanelProps {
  title?: string
  subtitle?: string
}

export function UserAdministrationPanel({ title, subtitle }: UserAdministrationPanelProps) {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const currentUser = useAuthStore((s) => s.user)
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<CompanyUser | null>(null)
  const [resetUser, setResetUser] = useState<CompanyUser | null>(null)
  const [featuresUser, setFeaturesUser] = useState<CompanyUser | null>(null)
  const deleteUser = useDeleteEntity('/users', ['company-users', 'settings-users'])

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['company-users'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<CompanyUser>>('/users', { params: { page_size: 100 } })
      return data
    },
  })

  const users = data?.items ?? []

  const stats = useMemo(() => ({
    total: users.length,
    active: users.filter((user) => user.status === 'active').length,
    suspended: users.filter((user) => user.status === 'suspended').length,
    admins: users.filter((user) => user.system_role === 'company_admin').length,
  }), [users])

  const toggleStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const action = status === 'active' ? 'suspend' : 'activate'
      await api.post(`/users/${id}/${action}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['company-users'] })
      qc.invalidateQueries({ queryKey: ['settings-users'] })
    },
  })

  const nameFor = (user: CompanyUser | Record<string, unknown>) => {
    const ar = String(user.full_name_ar ?? '')
    const en = String(user.full_name_en ?? '')
    return i18n.language === 'ar' ? ar || en : en || ar
  }

  return (
    <div>
      <div className="grid-stagger mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-primary-50 p-2 text-primary-700"><Users className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('total_users')}</p>
            <p className="text-xl font-bold">{stats.total}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-emerald-50 p-2 text-emerald-700"><UserCheck className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('active_users')}</p>
            <p className="text-xl font-bold">{stats.active}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-red-50 p-2 text-red-700"><UserX className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('suspended_users')}</p>
            <p className="text-xl font-bold">{stats.suspended}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-violet-50 p-2 text-violet-700"><ShieldCheck className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('company_admins')}</p>
            <p className="text-xl font-bold">{stats.admins}</p>
          </div>
        </Card>
      </div>

      <DataTable
        title={title ?? t('users')}
        subtitle={subtitle ?? t('company_users_admin_help')}
        loading={isLoading}
        exportFilename="company-users"
        data={users as unknown as Record<string, unknown>[]}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="me-2 h-4 w-4" />
            {t('add_user')}
          </Button>
        }
        emptyActionLabel={t('add_user')}
        onEmptyAction={() => setCreateOpen(true)}
        columns={[
          {
            key: 'full_name_en',
            label: t('user'),
            render: (row) => (
              <div>
                <p className="font-semibold text-slate-900">{nameFor(row)}</p>
                <p className="text-xs text-slate-500">{String(row.username ?? row.email ?? '')}</p>
              </div>
            ),
          },
          { key: 'email', label: t('email') },
          { key: 'phone', label: t('mobile') },
          { key: 'system_role', label: t('role'), render: (row) => <span className="capitalize">{formatRole(String(row.system_role ?? ''))}</span> },
          { key: 'status', label: t('status') },
        ]}
        rowActions={(row) => {
          const user = row as unknown as CompanyUser
          const isSelf = user.id === currentUser?.id
          return (
            <RowActions
              onEdit={() => setEditUser(user)}
              onDelete={!isSelf ? () => confirmDelete(t) && deleteUser.mutate(user.id, { onSuccess: () => refetch() }) : undefined}
              extra={
                <>
                  <Button
                    variant="secondary"
                    className="!px-2 !py-1.5 text-xs"
                    onClick={() => setFeaturesUser(user)}
                    title={t('user_feature_access')}
                  >
                    <Sliders className="me-1 h-3.5 w-3.5" />{t('authorizations')}
                  </Button>
                  <Button
                    variant="secondary"
                    className="!px-2 !py-1.5 text-xs"
                    onClick={() => setResetUser(user)}
                    title={t('reset_password')}
                  >
                    <KeyRound className="me-1 h-3.5 w-3.5" />{t('reset_password')}
                  </Button>
                  {!isSelf && (
                    <Button
                      variant="secondary"
                      className="!px-2 !py-1.5 text-xs"
                      loading={toggleStatus.isPending}
                      onClick={() => toggleStatus.mutate({ id: user.id, status: user.status })}
                    >
                      {user.status === 'active' ? t('suspend') : t('activate')}
                    </Button>
                  )}
                </>
              }
            />
          )
        }}
      />

      <UserFormModal open={createOpen} onClose={() => { setCreateOpen(false); refetch() }} />
      <UserEditModal
        open={!!editUser}
        user={editUser}
        showCompanyField={false}
        onClose={() => setEditUser(null)}
        onSaved={() => {
          qc.invalidateQueries({ queryKey: ['company-users'] })
          qc.invalidateQueries({ queryKey: ['settings-users'] })
        }}
      />
      <ResetPasswordModal
        open={!!resetUser}
        userId={resetUser?.id ?? null}
        userEmail={resetUser?.email ?? ''}
        onClose={() => setResetUser(null)}
      />
      <UserFeaturesModal
        open={!!featuresUser}
        userId={featuresUser?.id ?? 0}
        userName={featuresUser ? nameFor(featuresUser) : ''}
        onClose={() => setFeaturesUser(null)}
        onSaved={() => refetch()}
      />
    </div>
  )
}
