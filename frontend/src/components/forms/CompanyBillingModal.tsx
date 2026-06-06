import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import type { CompanyWithBilling } from '@/types'

interface CompanyBillingModalProps {
  open: boolean
  onClose: () => void
  company: CompanyWithBilling | null
  onSaved: () => void
}

export function CompanyBillingModal({ open, onClose, company, onSaved }: CompanyBillingModalProps) {
  const { t, i18n } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [reminderLoading, setReminderLoading] = useState(false)
  const [paymentAmount, setPaymentAmount] = useState('')
  const [form, setForm] = useState({
    billing_cycle: 'monthly',
    payment_terms_days: 30,
    next_billing_date: '',
    payment_status: 'pending',
    amount_due: '',
  })

  useEffect(() => {
    if (company?.billing && open) {
      setForm({
        billing_cycle: company.billing.billing_cycle,
        payment_terms_days: company.billing.payment_terms_days,
        next_billing_date: company.billing.next_billing_date ?? '',
        payment_status: company.billing.payment_status,
        amount_due: company.billing.amount_due != null ? String(company.billing.amount_due) : '',
      })
      setPaymentAmount(company.billing.amount_due != null ? String(company.billing.amount_due) : '')
    }
  }, [company, open])

  if (!company) return null

  const billing = company.billing
  const planLabel = i18n.language === 'ar'
    ? billing?.plan_name_ar || billing?.plan_name_en
    : billing?.plan_name_en || billing?.plan_name_ar

  const saveBilling = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.put(`/super-admin/companies/${company.id}/billing`, {
        ...form,
        payment_terms_days: Number(form.payment_terms_days),
        amount_due: form.amount_due ? Number(form.amount_due) : undefined,
      })
      onSaved()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  const recordPayment = async () => {
    if (!paymentAmount) return
    setLoading(true)
    try {
      await api.post(`/super-admin/companies/${company.id}/billing/record-payment`, {
        amount: Number(paymentAmount),
      })
      onSaved()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  const sendReminder = async () => {
    setReminderLoading(true)
    try {
      await api.post(`/super-admin/companies/${company.id}/billing/send-reminder`)
      onSaved()
    } finally {
      setReminderLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('billing_and_payment')} className="max-w-2xl">
      <div className="mb-4 rounded-lg bg-slate-50 p-4 text-sm">
        <p className="font-semibold text-slate-900">
          {i18n.language === 'ar' ? company.name_ar : company.name_en}
        </p>
        <p className="text-slate-600">{t('subscription_plan')}: {planLabel || '—'}</p>
        {billing?.payment_status === 'trial' && billing.end_date && (
          <p className="text-amber-700">{t('trial_ends')}: {billing.end_date}</p>
        )}
        {billing?.last_reminder_sent_at && (
          <p className="mt-1 text-xs text-slate-500">
            {t('last_reminder_sent')}: {new Date(billing.last_reminder_sent_at).toLocaleString(i18n.language === 'ar' ? 'ar-EG' : 'en-GB')}
          </p>
        )}
      </div>

      <form onSubmit={saveBilling} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">{t('billing_cycle')}</label>
            <select className="input-field" value={form.billing_cycle} onChange={(e) => setForm({ ...form, billing_cycle: e.target.value })}>
              <option value="monthly">{t('monthly')}</option>
              <option value="yearly">{t('yearly')}</option>
            </select>
          </div>
          <Input
            label={t('payment_terms_days')}
            type="number"
            min={0}
            max={90}
            value={form.payment_terms_days}
            onChange={(e) => setForm({ ...form, payment_terms_days: Number(e.target.value) })}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label={t('next_billing_date')}
            type="date"
            value={form.next_billing_date}
            onChange={(e) => setForm({ ...form, next_billing_date: e.target.value })}
          />
          <Input
            label={t('amount_due')}
            type="number"
            value={form.amount_due}
            onChange={(e) => setForm({ ...form, amount_due: e.target.value })}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">{t('payment_status')}</label>
          <select className="input-field" value={form.payment_status} onChange={(e) => setForm({ ...form, payment_status: e.target.value })}>
            <option value="trial">{t('trial')}</option>
            <option value="paid">{t('paid')}</option>
            <option value="pending">{t('pending')}</option>
            <option value="overdue">{t('overdue')}</option>
          </select>
        </div>
        <div className="flex flex-wrap gap-3 border-t border-slate-200 pt-4">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" loading={reminderLoading} onClick={sendReminder}>
            {t('send_payment_reminder')}
          </Button>
        </div>
      </form>

      <div className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
        <h4 className="mb-2 font-medium text-emerald-900">{t('record_payment')}</h4>
        <div className="flex flex-wrap items-end gap-3">
          <Input
            label={t('amount')}
            type="number"
            value={paymentAmount}
            onChange={(e) => setPaymentAmount(e.target.value)}
          />
          <Button type="button" onClick={recordPayment} loading={loading}>{t('record_payment')}</Button>
        </div>
      </div>
    </Modal>
  )
}
