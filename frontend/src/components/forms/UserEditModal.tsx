import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import { ASSIGNABLE_ROLES } from '@/lib/roles'
import { useAuthStore } from '@/stores/authStore'

interface AdminUser {
  id: number
  username?: string
  email: string
  full_name_ar: string
  full_name_en: string
  system_role: string
  status: string
  company_id?: number
  is_super_admin: boolean
}

interface UserEditModalProps {
  open: boolean
  onClose: () => void
  user: AdminUser | null
  onSaved: () => void
  hideCompanyId?: boolean
}

export function UserEditModal({ open, onClose, user, onSaved, hideCompanyId }: UserEditModalProps) {
  const { t } = useTranslation()
  const currentUser = useAuthStore((s) => s.user)
  const showCompanyId = !hideCompanyId && currentUser?.is_super_admin
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    username: '',
    email: '',
    full_name_ar: '',
    full_name_en: '',
    system_role: 'sales_agent',
    company_id: '' as string | number,
  })

  useEffect(() => {
    if (user && open) {
      setForm({
        username: user.username ?? '',
        email: user.email,
        full_name_ar: user.full_name_ar,
        full_name_en: user.full_name_en,
        system_role: user.system_role,
        company_id: user.company_id ?? '',
      })
    }
  }, [user, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    setLoading(true)
    try {
      await api.put(`/users/${user.id}`, {
        username: form.username.trim().toLowerCase(),
        email: form.email,
        full_name_ar: form.full_name_ar,
        full_name_en: form.full_name_en,
        system_role: form.system_role,
        company_id: form.company_id ? Number(form.company_id) : undefined,
      })
      onSaved()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('edit_user')} className="max-w-lg">
      {user && (
        <form onSubmit={submit} className="space-y-4">
          <Input label={t('username')} value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value.toLowerCase() })} required placeholder="demo_admin" />
          <Input label={t('email')} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <Input label={t('name_ar')} value={form.full_name_ar} onChange={(e) => setForm({ ...form, full_name_ar: e.target.value })} required />
          <Input label={t('name_en')} value={form.full_name_en} onChange={(e) => setForm({ ...form, full_name_en: e.target.value })} required />
          <div>
            <label className="mb-1 block text-sm font-medium">{t('role')}</label>
            <select className="input-field" value={form.system_role} onChange={(e) => setForm({ ...form, system_role: e.target.value })}>
              {ASSIGNABLE_ROLES.map((r) => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          {showCompanyId && (
            <Input label={t('company_id')} type="number" value={form.company_id} onChange={(e) => setForm({ ...form, company_id: e.target.value })} />
          )}
          <div className="flex gap-3">
            <Button type="submit" loading={loading}>{t('save')}</Button>
            <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
          </div>
        </form>
      )}
    </Modal>
  )
}
