import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import type { Company } from '@/types'

interface CompanyEditModalProps {
  open: boolean
  onClose: () => void
  company: Company | null
  onSaved: () => void
}

export function CompanyEditModal({ open, onClose, company, onSaved }: CompanyEditModalProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    name_ar: '',
    name_en: '',
    email: '',
    phone: '',
    city: '',
    country: 'Egypt',
    status: 'active',
  })

  useEffect(() => {
    if (company && open) {
      setForm({
        name_ar: company.name_ar,
        name_en: company.name_en,
        email: (company as Company & { email?: string }).email ?? '',
        phone: (company as Company & { phone?: string }).phone ?? '',
        city: (company as Company & { city?: string }).city ?? '',
        country: company.country ?? 'Egypt',
        status: company.status,
      })
    }
  }, [company, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!company) return
    setLoading(true)
    try {
      await api.put(`/super-admin/companies/${company.id}`, form)
      onSaved()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('edit_company')} className="max-w-xl">
      {company && (
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
            <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
          </div>
          <Input label={t('email')} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input label={t('mobile')} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label={t('city')} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            <Input label={t('country')} value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">{t('status')}</label>
            <select className="input-field" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="active">{t('active')}</option>
              <option value="trial">{t('trial')}</option>
              <option value="suspended">{t('suspended')}</option>
              <option value="expired">{t('expired')}</option>
            </select>
          </div>
          <div className="flex gap-3">
            <Button type="submit" loading={loading}>{t('save')}</Button>
            <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
          </div>
        </form>
      )}
    </Modal>
  )
}
