import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import type { Paginated } from '@/types'

interface AdminUser {
  id: number
  email: string
  full_name_ar: string
  full_name_en: string
  system_role: string
  status: string
  company_id?: number
  is_super_admin: boolean
}

export function SuperAdminUsersPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['super-admin-users'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<AdminUser>>('/users', { params: { page_size: 100 } })
      return data
    },
  })

  const toggleStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const action = status === 'active' ? 'suspend' : 'activate'
      await api.post(`/users/${id}/${action}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['super-admin-users'] }),
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('users')}</h1>
      <Card>
        {isLoading ? (
          <p className="text-slate-500">{t('loading')}</p>
        ) : data?.items.length === 0 ? (
          <p className="text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-3 text-start font-medium">#</th>
                  <th className="pb-3 text-start font-medium">{t('email')}</th>
                  <th className="pb-3 text-start font-medium">{t('name_ar')}</th>
                  <th className="pb-3 text-start font-medium">{t('role')}</th>
                  <th className="pb-3 text-start font-medium">{t('status')}</th>
                  <th className="pb-3 text-start font-medium">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((user) => (
                  <tr key={user.id} className="border-b border-slate-100">
                    <td className="py-3">{user.id}</td>
                    <td className="py-3">{user.email}</td>
                    <td className="py-3 font-medium">
                      {i18n.language === 'ar' ? user.full_name_ar : user.full_name_en}
                    </td>
                    <td className="py-3">
                      {user.is_super_admin ? t('super_admin') : user.system_role.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                        user.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="py-3">
                      {!user.is_super_admin && (
                        <Button
                          variant="secondary"
                          loading={toggleStatus.isPending}
                          onClick={() => toggleStatus.mutate({ id: user.id, status: user.status })}
                        >
                          {user.status === 'active' ? t('suspend') : t('activate')}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
