import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Plus, Calculator, CheckCircle, Banknote } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { StatCard } from '@/components/ui/StatCard'
import { EmptyState } from '@/components/ui/EmptyState'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { useProjectsLookup } from '@/hooks/useLookupData'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

function SelectField({ label, value, onChange, options, required }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  required?: boolean
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      <select className="input-field" value={value} onChange={(e) => onChange(e.target.value)} required={required}>
        <option value="">—</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

export function CashFlowPanel() {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const { data: projects = [] } = useProjectsLookup()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    transaction_date: new Date().toISOString().slice(0, 10),
    transaction_type: 'income',
    category: '',
    description: '',
    amount: '',
    payment_method: 'cash',
    project_id: '',
  })

  const { data: summary } = useQuery({
    queryKey: ['cash-flow-summary'],
    queryFn: async () => (await api.get('/treasury/cash-transactions/summary')).data,
  })

  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ['cash-transactions'],
    queryFn: async () => (await api.get('/treasury/cash-transactions')).data,
  })

  const createTxn = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.post('/treasury/cash-transactions', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cash-transactions'] })
      qc.invalidateQueries({ queryKey: ['cash-flow-summary'] })
      setOpen(false)
    },
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    createTxn.mutate({
      ...form,
      amount: form.amount,
      project_id: form.project_id ? Number(form.project_id) : undefined,
      description: form.description || undefined,
    })
  }

  return (
    <div>
      <div className="mb-4 grid gap-4 md:grid-cols-3">
        <StatCard title={t('total_income')} value={formatEGP(summary?.total_income)} icon={Banknote} color="bg-emerald-50 text-emerald-700" />
        <StatCard title={t('total_expenses')} value={formatEGP(summary?.total_expense)} icon={Banknote} color="bg-red-50 text-red-700" />
        <StatCard title={t('net_cash_flow')} value={formatEGP(summary?.net_cash_flow)} icon={Banknote} color="bg-primary-50 text-primary-700" />
      </div>
      <div className="mb-4 flex justify-end">
        <Button onClick={() => setOpen(true)}><Plus className="me-2 h-4 w-4" />{t('add_cash_transaction')}</Button>
      </div>
      {isLoading ? (
        <p className="text-slate-500">{t('loading')}</p>
      ) : transactions.length === 0 ? (
        <EmptyState title={t('no_cash_transactions')} description={t('no_cash_transactions_help')} />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head-gradient">
                <th className="px-4 py-3 text-start">{t('date')}</th>
                <th className="px-4 py-3 text-start">{t('type')}</th>
                <th className="px-4 py-3 text-start">{t('category')}</th>
                <th className="px-4 py-3 text-start">{t('description')}</th>
                <th className="px-4 py-3 text-start">{t('amount')}</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn: Record<string, unknown>) => (
                <tr key={txn.id as number} className="border-t border-slate-100">
                  <td className="px-4 py-3">{String(txn.transaction_date)}</td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      'rounded-full px-2 py-0.5 text-xs font-medium',
                      txn.transaction_type === 'income' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700',
                    )}>
                      {txn.transaction_type === 'income' ? t('income') : t('expense')}
                    </span>
                  </td>
                  <td className="px-4 py-3">{String(txn.category)}</td>
                  <td className="px-4 py-3 text-slate-600">{String(txn.description ?? '')}</td>
                  <td className="px-4 py-3 font-medium">{formatEGP(txn.amount as number)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Modal open={open} onClose={() => setOpen(false)} title={t('add_cash_transaction')}>
        <form onSubmit={submit} className="space-y-4">
          <Input label={t('date')} type="date" value={form.transaction_date} onChange={(e) => setForm({ ...form, transaction_date: e.target.value })} required />
          <SelectField label={t('type')} value={form.transaction_type} onChange={(v) => setForm({ ...form, transaction_type: v })} required options={[
            { value: 'income', label: t('income') },
            { value: 'expense', label: t('expense') },
          ]} />
          <Input label={t('category')} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required />
          <Input label={t('description')} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Input label={t('amount')} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          <SelectField label={t('payment_method')} value={form.payment_method} onChange={(v) => setForm({ ...form, payment_method: v })} options={[
            { value: 'cash', label: t('cash') },
            { value: 'bank_transfer', label: t('bank_transfer') },
            { value: 'cheque', label: t('cheque') },
          ]} />
          <SelectField label={t('projects')} value={form.project_id} onChange={(v) => setForm({ ...form, project_id: v })}
            options={projects.map((p) => ({ value: String(p.id), label: String(p.name_ar) }))} />
          <div className="flex gap-3 pt-2">
            <Button type="submit" loading={createTxn.isPending}>{t('save')}</Button>
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>{t('cancel')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export function ChequesPanel() {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const today = new Date().toISOString().slice(0, 10)
  const [form, setForm] = useState({
    direction: 'received',
    cheque_number: '',
    bank_name: '',
    drawer_name: '',
    payee_name: '',
    amount: '',
    issue_date: today,
    due_date: today,
    notes: '',
  })

  const { data: cheques = [], isLoading } = useQuery({
    queryKey: ['cheques'],
    queryFn: async () => (await api.get('/treasury/cheques')).data,
  })

  const { data: dueSoon = [] } = useQuery({
    queryKey: ['cheques-due-soon'],
    queryFn: async () => (await api.get('/treasury/cheques', { params: { due_within_days: 14 } })).data,
  })

  const createCheque = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.post('/treasury/cheques', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cheques'] })
      qc.invalidateQueries({ queryKey: ['cheques-due-soon'] })
      setOpen(false)
    },
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.put(`/treasury/cheques/${id}`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cheques'] })
      qc.invalidateQueries({ queryKey: ['cheques-due-soon'] })
    },
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    createCheque.mutate({
      ...form,
      amount: form.amount,
      drawer_name: form.drawer_name || undefined,
      payee_name: form.payee_name || undefined,
      notes: form.notes || undefined,
    })
  }

  const statusColor = (s: string) => {
    if (s === 'cleared') return 'bg-emerald-50 text-emerald-700'
    if (s === 'bounced') return 'bg-red-50 text-red-700'
    if (s === 'pending') return 'bg-amber-50 text-amber-700'
    return 'bg-slate-100 text-slate-700'
  }

  return (
    <div>
      {dueSoon.length > 0 && (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {t('cheques_due_soon', { count: dueSoon.length })}
        </div>
      )}
      <div className="mb-4 flex justify-end">
        <Button onClick={() => setOpen(true)}><Plus className="me-2 h-4 w-4" />{t('add_cheque')}</Button>
      </div>
      {isLoading ? (
        <p className="text-slate-500">{t('loading')}</p>
      ) : cheques.length === 0 ? (
        <EmptyState title={t('no_cheques')} description={t('no_cheques_help')} />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head-gradient">
                <th className="px-4 py-3 text-start">#</th>
                <th className="px-4 py-3 text-start">{t('bank')}</th>
                <th className="px-4 py-3 text-start">{t('due_date')}</th>
                <th className="px-4 py-3 text-start">{t('amount')}</th>
                <th className="px-4 py-3 text-start">{t('status')}</th>
                <th className="px-4 py-3 text-start">{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {cheques.map((c: Record<string, unknown>) => (
                <tr key={c.id as number} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium">{String(c.cheque_number)}</td>
                  <td className="px-4 py-3">{String(c.bank_name)}</td>
                  <td className="px-4 py-3">{String(c.due_date)}</td>
                  <td className="px-4 py-3">{formatEGP(c.amount as number)}</td>
                  <td className="px-4 py-3">
                    <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', statusColor(String(c.status)))}>
                      {String(c.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {c.status === 'pending' && (
                      <div className="flex gap-2">
                        <button type="button" onClick={() => updateStatus.mutate({ id: c.id as number, status: 'cleared' })} className="text-xs text-emerald-600 hover:underline">{t('mark_cleared')}</button>
                        <button type="button" onClick={() => updateStatus.mutate({ id: c.id as number, status: 'bounced' })} className="text-xs text-red-600 hover:underline">{t('mark_bounced')}</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Modal open={open} onClose={() => setOpen(false)} title={t('add_cheque')}>
        <form onSubmit={submit} className="space-y-4">
          <SelectField label={t('direction')} value={form.direction} onChange={(v) => setForm({ ...form, direction: v })} required options={[
            { value: 'received', label: t('cheque_received') },
            { value: 'issued', label: t('cheque_issued') },
          ]} />
          <Input label={t('cheque_number')} value={form.cheque_number} onChange={(e) => setForm({ ...form, cheque_number: e.target.value })} required />
          <Input label={t('bank')} value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} required />
          <Input label={t('drawer')} value={form.drawer_name} onChange={(e) => setForm({ ...form, drawer_name: e.target.value })} />
          <Input label={t('payee')} value={form.payee_name} onChange={(e) => setForm({ ...form, payee_name: e.target.value })} />
          <Input label={t('amount')} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          <Input label={t('issue_date')} type="date" value={form.issue_date} onChange={(e) => setForm({ ...form, issue_date: e.target.value })} required />
          <Input label={t('due_date')} type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} required />
          <div className="flex gap-3 pt-2">
            <Button type="submit" loading={createCheque.isPending}>{t('save')}</Button>
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>{t('cancel')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export function ProgressBillingsPanel() {
  const { t } = useTranslation()
  const { formatEGP, formatInteger } = useFormatNumber()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [calcPreview, setCalcPreview] = useState<Record<string, number> | null>(null)
  const today = new Date().toISOString().slice(0, 10)
  const [form, setForm] = useState({
    agreement_id: '',
    certificate_number: '',
    period_from: today,
    period_to: today,
    progress_percent: '30',
    other_deductions: '0',
    notes: '',
  })

  const { data: agreements = [] } = useQuery({
    queryKey: ['subcontract-agreements'],
    queryFn: async () => (await api.get('/treasury/subcontract-agreements')).data,
  })

  const { data: certificates = [], isLoading } = useQuery({
    queryKey: ['progress-certificates'],
    queryFn: async () => (await api.get('/treasury/progress-certificates')).data,
  })

  const createCert = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.post('/treasury/progress-certificates', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['progress-certificates'] })
      qc.invalidateQueries({ queryKey: ['cash-transactions'] })
      qc.invalidateQueries({ queryKey: ['cash-flow-summary'] })
      setOpen(false)
      setCalcPreview(null)
    },
  })

  const approveCert = useMutation({
    mutationFn: (id: number) => api.post(`/treasury/progress-certificates/${id}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['progress-certificates'] }),
  })

  const payCert = useMutation({
    mutationFn: (id: number) => api.post(`/treasury/progress-certificates/${id}/pay`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['progress-certificates'] })
      qc.invalidateQueries({ queryKey: ['cash-transactions'] })
      qc.invalidateQueries({ queryKey: ['cash-flow-summary'] })
    },
  })

  const runCalculate = async () => {
    if (!form.agreement_id) return
    const { data } = await api.post('/treasury/progress-certificates/calculate', {
      agreement_id: Number(form.agreement_id),
      progress_percent: Number(form.progress_percent),
      other_deductions: form.other_deductions || 0,
    })
    setCalcPreview(data)
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    createCert.mutate({
      agreement_id: Number(form.agreement_id),
      certificate_number: form.certificate_number,
      period_from: form.period_from,
      period_to: form.period_to,
      progress_percent: Number(form.progress_percent),
      other_deductions: form.other_deductions || 0,
      notes: form.notes || undefined,
    })
  }

  const statusLabel = (s: string) => t(`cert_status_${s}`, s)

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <Button onClick={() => setOpen(true)}><Plus className="me-2 h-4 w-4" />{t('add_progress_certificate')}</Button>
      </div>
      {isLoading ? (
        <p className="text-slate-500">{t('loading')}</p>
      ) : certificates.length === 0 ? (
        <EmptyState title={t('no_progress_certificates')} description={t('no_progress_certificates_help')} />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head-gradient">
                <th className="px-4 py-3 text-start">#</th>
                <th className="px-4 py-3 text-start">{t('subcontractor')}</th>
                <th className="px-4 py-3 text-start">{t('progress')}</th>
                <th className="px-4 py-3 text-start">{t('gross_amount')}</th>
                <th className="px-4 py-3 text-start">{t('retention')}</th>
                <th className="px-4 py-3 text-start">{t('net_payable')}</th>
                <th className="px-4 py-3 text-start">{t('status')}</th>
                <th className="px-4 py-3 text-start">{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {certificates.map((c: Record<string, unknown>) => (
                <tr key={c.id as number} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium">{String(c.certificate_number)}</td>
                  <td className="px-4 py-3">{String(c.subcontractor_name ?? '')}</td>
                  <td className="px-4 py-3">{formatInteger(c.progress_percent as number)}%</td>
                  <td className="px-4 py-3">{formatEGP(c.current_gross as number)}</td>
                  <td className="px-4 py-3">{formatEGP(c.retention_amount as number)}</td>
                  <td className="px-4 py-3 font-semibold text-primary-700">{formatEGP(c.net_payable as number)}</td>
                  <td className="px-4 py-3">{statusLabel(String(c.status))}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {c.status === 'draft' && (
                        <button type="button" onClick={() => approveCert.mutate(c.id as number)} className="flex items-center gap-1 text-xs text-emerald-600 hover:underline">
                          <CheckCircle className="h-3 w-3" />{t('approve')}
                        </button>
                      )}
                      {c.status === 'approved' && (
                        <button type="button" onClick={() => payCert.mutate(c.id as number)} className="text-xs text-primary-600 hover:underline">{t('mark_paid')}</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Modal open={open} onClose={() => setOpen(false)} title={t('add_progress_certificate')} className="max-w-xl">
        <form onSubmit={submit} className="space-y-4">
          <SelectField label={t('subcontract_agreement')} value={form.agreement_id} onChange={(v) => setForm({ ...form, agreement_id: v })} required
            options={agreements.map((a: Record<string, unknown>) => ({
              value: String(a.id),
              label: `${a.contract_number} — ${a.subcontractor_name}`,
            }))} />
          <Input label={t('certificate_number')} value={form.certificate_number} onChange={(e) => setForm({ ...form, certificate_number: e.target.value })} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label={t('period_from')} type="date" value={form.period_from} onChange={(e) => setForm({ ...form, period_from: e.target.value })} required />
            <Input label={t('period_to')} type="date" value={form.period_to} onChange={(e) => setForm({ ...form, period_to: e.target.value })} required />
          </div>
          <Input label={t('progress_percent')} type="number" min={0} max={100} value={form.progress_percent} onChange={(e) => setForm({ ...form, progress_percent: e.target.value })} required />
          <Input label={t('other_deductions')} value={form.other_deductions} onChange={(e) => setForm({ ...form, other_deductions: e.target.value })} />
          <Button type="button" variant="secondary" onClick={() => runCalculate()}><Calculator className="me-2 h-4 w-4" />{t('billing_calculation')}</Button>
          {calcPreview && (
            <div className="rounded-lg border border-primary-100 bg-primary-50 p-3 text-sm">
              <p className="mb-2 flex items-center gap-2 font-medium text-primary-900">
                <Calculator className="h-4 w-4" />{t('billing_calculation')}
              </p>
              <div className="grid grid-cols-2 gap-2 text-slate-700">
                <span>{t('gross_amount')}:</span><span className="font-medium">{formatEGP(calcPreview.current_gross)}</span>
                <span>{t('retention')}:</span><span>{formatEGP(calcPreview.retention_amount)}</span>
                <span>{t('advance_deduction')}:</span><span>{formatEGP(calcPreview.advance_deduction)}</span>
                <span>{t('net_payable')}:</span><span className="font-semibold text-primary-800">{formatEGP(calcPreview.net_payable)}</span>
              </div>
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <Button type="submit" loading={createCert.isPending}>{t('save')}</Button>
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>{t('cancel')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
