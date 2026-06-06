import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Pencil, KeyRound, Users, Building2, AlertTriangle } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingState } from '@/components/ui/LoadingState'
import { Button } from '@/components/ui/Button'
import { UserEditModal } from '@/components/forms/UserEditModal'
import { ResetPasswordModal } from '@/components/forms/ResetPasswordModal'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import type { Paginated } from '@/types'

interface AdminUser {
  id: number
  username?: string
  email: string
  full_name_ar: string
  full_name_en: string
  system_role: string
  status: string
  company_id?: number
  company_name_ar?: string
  company_name_en?: string
  company_code?: string
  plan_name_ar?: string
  plan_name_en?: string
  payment_terms_days?: number
  next_billing_date?: string
  payment_status?: string
  amount_due?: number
  is_super_admin: boolean
}

function PaymentBadge({ status, t }: { status?: string; t: (k: string) => string }) {
  if (!status) return <span className="text-slate-400">—</span>
  const cls: Record<string, string> = {
    paid: 'status-paid', pending: 'status-pending', overdue: 'status-overdue', trial: 'status-pending',
  }
  return <span className={cls[status] || 'status-badge bg-slate-100 text-slate-600'}>{t(status)}</span>
}

export function SuperAdminUsersPage() {
  const { t, i18n } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const [editUser, setEditUser] = useState<AdminUser | null>(null)
  const [resetUser, setResetUser] = useState<AdminUser | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['super-admin-users'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<AdminUser>>('/users', { params: { page_size: 100 } })
      return data
    },
  })

  const stats = useMemo(() => {
    const items = data?.items ?? []
    const tenantUsers = items.filter((u) => !u.is_super_admin)
    return {
      total: items.length,
      active: tenantUsers.filter((u) => u.status === 'active').length,
      companies: new Set(tenantUsers.map((u) => u.company_id).filter(Boolean)).size,
      overdue: tenantUsers.filter((u) => u.payment_status === 'overdue').length,
    }
  }, [data])

  const toggleStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const action = status === 'active' ? 'suspend' : 'activate'
      await api.post(`/users/${id}/${action}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['super-admin-users'] }),
  })

  return (
    <div>
      <PageHeader title={t('users')} subtitle={t('users_admin_help')} icon={Users} accentIndex={3} />

      <div className="grid-stagger mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-primary-50 p-2 text-primary-700"><Users className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('total_users')}</p>
            <p className="text-xl font-bold">{stats.total}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-emerald-50 p-2 text-emerald-700"><Users className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('active_users')}</p>
            <p className="text-xl font-bold">{stats.active}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-sky-50 p-2 text-sky-700"><Building2 className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('companies_with_users')}</p>
            <p className="text-xl font-bold">{stats.companies}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-lg bg-red-50 p-2 text-red-700"><AlertTriangle className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500">{t('overdue_payments')}</p>
            <p className="text-xl font-bold text-red-600">{stats.overdue}</p>
          </div>
        </Card>
      </div>

      <Card>
        {isLoading ? (
          <LoadingState />
        ) : data?.items.length === 0 ? (
          <p className="text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1100px] text-sm">
              <thead>
                <tr className="table-head-gradient">
                  <th className="px-2 py-3 text-start">{t('user')}</th>
                  <th className="px-2 py-3 text-start">{t('role')}</th>
                  <th className="px-2 py-3 text-start">{t('company')}</th>
                  <th className="px-2 py-3 text-start">{t('subscription_plan')}</th>
                  <th className="px-2 py-3 text-start">{t('payment_terms')}</th>
                  <th className="px-2 py-3 text-start">{t('next_billing_date')}</th>
                  <th className="px-2 py-3 text-start">{t('payment_status')}</th>
                  <th className="px-2 py-3 text-start">{t('status')}</th>
                  <th className="px-2 py-3 text-start">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((user) => {
                  const name = i18n.language === 'ar' ? user.full_name_ar : user.full_name_en
                  const companyName = i18n.language === 'ar'
                    ? user.company_name_ar || user.company_name_en
                    : user.company_name_en || user.company_name_ar
                  const planName = i18n.language === 'ar'
                    ? user.plan_name_ar || user.plan_name_en
                    : user.plan_name_en || user.plan_name_ar
                  return (
                    <tr key={user.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                      <td className="px-2 py-4">
                        <p className="font-semibold text-slate-900">{name}</p>
                        <p className="text-xs text-slate-500">{user.username || user.email}</p>
                      </td>
                      <td className="px-2 py-4 capitalize">
                        {user.is_super_admin ? t('super_admin') : user.system_role.replace(/_/g, ' ')}
                      </td>
                      <td className="px-2 py-4">
                        {user.is_super_admin || !user.company_id ? (
                          <span className="text-slate-500">{t('platform')}</span>
                        ) : (
                          <div>
                            <p className="font-medium text-slate-800">{companyName}</p>
                            {user.company_code && <p className="text-xs text-slate-500">{user.company_code}</p>}
                          </div>
                        )}
                      </td>
                      <td className="px-2 py-4">{planName || '—'}</td>
                      <td className="px-2 py-4">
                        {user.payment_terms_days != null ? t('net_days', { days: user.payment_terms_days }) : '—'}
                      </td>
                      <td className="px-2 py-4">{user.next_billing_date || '—'}</td>
                      <td className="px-2 py-4">
                        {user.is_super_admin ? '—' : (
                          <div className="space-y-1">
                            <PaymentBadge status={user.payment_status} t={t} />
                            {user.amount_due != null && (
                              <p className="text-xs text-slate-500">{formatEGP(user.amount_due)}</p>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-2 py-4">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                          user.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                        }`}>
                          {t(user.status)}
                        </span>
                      </td>
                      <td className="px-2 py-4">
                        {!user.is_super_admin && (
                          <div className="flex flex-wrap gap-1.5">
                            <Button variant="secondary" onClick={() => setEditUser(user)}>
                              <Pencil className="me-1 h-4 w-4" />{t('edit')}
                            </Button>
                            <Button variant="secondary" onClick={() => setResetUser(user)}>
                              <KeyRound className="me-1 h-4 w-4" />{t('reset_password')}
                            </Button>
                            <Button
                              variant="secondary"
                              loading={toggleStatus.isPending}
                              onClick={() => toggleStatus.mutate({ id: user.id, status: user.status })}
                            >
                              {user.status === 'active' ? t('suspend') : t('activate')}
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <UserEditModal open={!!editUser} user={editUser} onClose={() => setEditUser(null)} onSaved={() => qc.invalidateQueries({ queryKey: ['super-admin-users'] })} />
      <ResetPasswordModal open={!!resetUser} userId={resetUser?.id ?? null} userEmail={resetUser?.email ?? ''} onClose={() => setResetUser(null)} />
    </div>
  )
}
