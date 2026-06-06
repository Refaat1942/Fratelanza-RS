import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'

interface CustomerEdit {
  id: number
  full_name_ar: string
  full_name_en: string
  mobile: string
  email?: string
  whatsapp?: string
  city?: string
  national_id?: string
  notes?: string
}

interface ClientFormModalProps {
  open: boolean
  onClose: () => void
  editCustomer?: CustomerEdit | null
}

export function ClientFormModal({ open, onClose, editCustomer }: ClientFormModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    full_name_ar: '',
    full_name_en: '',
    mobile: '',
    email: '',
    whatsapp: '',
    city: '',
    national_id: '',
    source: 'walk_in',
    notes: '',
    create_lead: true,
  })

  useEffect(() => {
    if (editCustomer && open) {
      setForm({
        full_name_ar: editCustomer.full_name_ar,
        full_name_en: editCustomer.full_name_en,
        mobile: editCustomer.mobile,
        email: editCustomer.email ?? '',
        whatsapp: editCustomer.whatsapp ?? '',
        city: editCustomer.city ?? '',
        national_id: editCustomer.national_id ?? '',
        source: 'walk_in',
        notes: editCustomer.notes ?? '',
        create_lead: false,
      })
    } else if (open && !editCustomer) {
      setForm({ full_name_ar: '', full_name_en: '', mobile: '', email: '', whatsapp: '', city: '', national_id: '', source: 'walk_in', notes: '', create_lead: true })
    }
  }, [editCustomer, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (editCustomer) {
        await api.put(`/customers/${editCustomer.id}`, {
          full_name_ar: form.full_name_ar,
          full_name_en: form.full_name_en,
          mobile: form.mobile,
          email: form.email || undefined,
          whatsapp: form.whatsapp || undefined,
          city: form.city || undefined,
          national_id: form.national_id || undefined,
          notes: form.notes || undefined,
        })
      } else {
        await api.post('/customers/onboard', form)
        qc.invalidateQueries({ queryKey: ['leads'] })
      }
      qc.invalidateQueries({ queryKey: ['customers'] })
      onClose()
      if (!editCustomer) {
        setForm({ full_name_ar: '', full_name_en: '', mobile: '', email: '', whatsapp: '', city: '', national_id: '', source: 'walk_in', notes: '', create_lead: true })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editCustomer ? t('edit_customer') : t('add_client')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('name_ar')} value={form.full_name_ar} onChange={(e) => setForm({ ...form, full_name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.full_name_en} onChange={(e) => setForm({ ...form, full_name_en: e.target.value })} required />
        <Input label={t('mobile')} value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} required />
        <Input label={t('email')} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <Input label="WhatsApp" value={form.whatsapp} onChange={(e) => setForm({ ...form, whatsapp: e.target.value })} />
        <Input label={t('city')} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
        <Input label={t('national_id')} value={form.national_id} onChange={(e) => setForm({ ...form, national_id: e.target.value })} />
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">{t('lead_source')}</label>
          <select className="input-field" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}>
            <option value="walk_in">Walk In</option>
            <option value="facebook">Facebook</option>
            <option value="instagram">Instagram</option>
            <option value="referral">Referral</option>
            <option value="broker">Broker</option>
            <option value="website">Website</option>
          </select>
        </div>
        {!editCustomer && (
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.create_lead} onChange={(e) => setForm({ ...form, create_lead: e.target.checked })} />
            {t('create_lead_auto')}
          </label>
        )}
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
