import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

interface UserFormModalProps {
  open: boolean
  onClose: () => void
}

const ROLES = ['sales_agent', 'sales_manager', 'collection_officer', 'accountant', 'company_admin', 'customer_service']

export function UserFormModal({ open, onClose }: UserFormModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name_ar: '',
    full_name_en: '',
    system_role: 'sales_agent',
    phone: '',
  })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/users', { ...form, company_id: user?.company_id })
      qc.invalidateQueries({ queryKey: ['users'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('add_user')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('username')} value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value.toLowerCase() })} required placeholder="sales_agent_1" />
        <Input label={t('email')} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <Input label={t('password')} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <Input label={t('name_ar')} value={form.full_name_ar} onChange={(e) => setForm({ ...form, full_name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.full_name_en} onChange={(e) => setForm({ ...form, full_name_en: e.target.value })} required />
        <Input label={t('mobile')} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">{t('role')}</label>
          <select className="input-field" value={form.system_role} onChange={(e) => setForm({ ...form, system_role: e.target.value })}>
            {ROLES.map((r) => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
          </select>
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
