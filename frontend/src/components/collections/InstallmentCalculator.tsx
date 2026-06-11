import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Calculator, RefreshCw, Save } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { useListData } from '@/hooks/useListData'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type ScheduleRow = {
  installment_number: number
  due_date: string
  due_amount: number
  remaining_balance: number
  is_manual: boolean
  paid_amount?: number
}

function SelectField({ label, value, onChange, options }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      <select className="input-field" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

export function InstallmentCalculator() {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const today = new Date().toISOString().slice(0, 10)
  const { items: contracts = [] } = useListData<Record<string, unknown>>('contracts', '/contracts')

  const [form, setForm] = useState({
    total_price: '2500000',
    down_payment: '500000',
    plan_type: 'quarterly',
    number_of_installments: '8',
    start_date: today,
    contract_id: '',
  })
  const [schedule, setSchedule] = useState<ScheduleRow[]>([])
  const [error, setError] = useState('')

  const generate = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/collections/calculator/preview', {
        total_price: form.total_price,
        down_payment: form.down_payment,
        plan_type: form.plan_type,
        number_of_installments: Number(form.number_of_installments),
        start_date: form.start_date,
      })
      return data
    },
    onSuccess: (data) => {
      setSchedule(data.installments as ScheduleRow[])
      setError('')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(String(msg ?? t('error')))
    },
  })

  const recalculate = useMutation({
    mutationFn: async (rows: ScheduleRow[]) => {
      const { data } = await api.post('/collections/calculator/recalculate', {
        total_price: form.total_price,
        down_payment: form.down_payment,
        plan_type: form.plan_type,
        start_date: form.start_date,
        installments: rows.map((r) => ({
          installment_number: r.installment_number,
          due_date: r.due_date,
          due_amount: r.due_amount,
          paid_amount: r.paid_amount ?? 0,
          is_manual: r.is_manual,
        })),
      })
      return data
    },
    onSuccess: (data) => {
      setSchedule(data.installments as ScheduleRow[])
      setError('')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(String(msg ?? t('error')))
    },
  })

  const apply = useMutation({
    mutationFn: async () => {
      if (!form.contract_id) throw new Error(t('select_contract'))
      const { data } = await api.post('/collections/calculator/apply', {
        contract_id: Number(form.contract_id),
        plan_type: form.plan_type,
        down_payment: form.down_payment,
        start_date: form.start_date,
        installments: schedule.map((r) => ({
          installment_number: r.installment_number,
          due_date: r.due_date,
          due_amount: r.due_amount,
          paid_amount: r.paid_amount ?? 0,
          is_manual: r.is_manual,
        })),
      })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['installments'] })
      setError('')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(String(msg ?? t('error')))
    },
  })

  const loadContractPlan = useQuery({
    queryKey: ['payment-plan', form.contract_id],
    enabled: Boolean(form.contract_id),
    queryFn: async () => {
      const { data } = await api.get(`/collections/payment-plans/${form.contract_id}`)
      return data
    },
    retry: false,
  })

  useEffect(() => {
    if (loadContractPlan.data && form.contract_id) {
      const plan = loadContractPlan.data as Record<string, unknown>
      setForm((f) => ({
        ...f,
        total_price: String(plan.total_price ?? f.total_price),
        down_payment: String(plan.down_payment ?? f.down_payment),
        plan_type: String(plan.plan_type ?? f.plan_type),
        number_of_installments: String(plan.number_of_installments ?? f.number_of_installments),
        start_date: String(plan.start_date ?? f.start_date),
      }))
      setSchedule((plan.installments as ScheduleRow[]) ?? [])
    }
  }, [loadContractPlan.data, form.contract_id])

  const updateAmountLocal = (index: number, value: string) => {
    setSchedule((rows) =>
      rows.map((row, i) => (i === index ? { ...row, due_amount: value === '' ? 0 : Number(value) } : row)),
    )
  }

  const commitAmount = (index: number) => {
    const row = schedule[index]
    if (!row) return
    const amount = Number(row.due_amount)
    if (Number.isNaN(amount) || amount < 0) return
    const next = schedule.map((r, i) =>
      i === index ? { ...r, due_amount: amount, is_manual: true } : r,
    )
    recalculate.mutate(next)
  }

  const financed = Number(form.total_price) - Number(form.down_payment)
  const scheduleTotal = schedule.reduce((s, r) => s + Number(r.due_amount), 0)
  const balanced = Math.abs(scheduleTotal - financed) < 0.02

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-primary-200 bg-gradient-to-br from-primary-50 to-white p-5">
        <div className="mb-4 flex items-center gap-2 text-primary-900">
          <Calculator className="h-5 w-5" />
          <p className="font-semibold">{t('installment_calculator_title')}</p>
        </div>
        <p className="text-sm text-slate-600">{t('installment_calculator_help')}</p>
      </div>

      <div className="grid gap-4 rounded-xl border border-slate-200 bg-white p-5 lg:grid-cols-3">
        <Input
          label={t('unit_total_price')}
          value={form.total_price}
          onChange={(e) => setForm({ ...form, total_price: e.target.value })}
        />
        <Input
          label={t('down_payment')}
          value={form.down_payment}
          onChange={(e) => setForm({ ...form, down_payment: e.target.value })}
        />
        <Input
          label={t('financed_amount')}
          value={String(financed)}
          readOnly
        />
        <SelectField
          label={t('payment_frequency')}
          value={form.plan_type}
          onChange={(v) => setForm({ ...form, plan_type: v })}
          options={[
            { value: 'monthly', label: t('monthly') },
            { value: 'quarterly', label: t('quarterly') },
            { value: 'semi_annual', label: t('semi_annual') },
            { value: 'annual', label: t('annual') },
          ]}
        />
        <Input
          label={t('number_of_installments')}
          type="number"
          min={1}
          value={form.number_of_installments}
          onChange={(e) => setForm({ ...form, number_of_installments: e.target.value })}
        />
        <Input
          label={t('first_due_date')}
          type="date"
          value={form.start_date}
          onChange={(e) => setForm({ ...form, start_date: e.target.value })}
        />
        <SelectField
          label={t('apply_to_contract')}
          value={form.contract_id}
          onChange={(v) => setForm({ ...form, contract_id: v })}
          options={[
            { value: '', label: '—' },
            ...contracts.map((c) => ({
              value: String(c.id),
              label: `${c.contract_number} — ${formatEGP(c.total_price as number)}`,
            })),
          ]}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => generate.mutate()} loading={generate.isPending}>
          <RefreshCw className="me-2 h-4 w-4" />{t('generate_schedule')}
        </Button>
        {schedule.length > 0 && form.contract_id && (
          <Button variant="secondary" onClick={() => apply.mutate()} loading={apply.isPending}>
            <Save className="me-2 h-4 w-4" />{t('save_to_contract')}
          </Button>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {schedule.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
              <p className="text-slate-500">{t('financed_amount')}</p>
              <p className="text-lg font-semibold text-slate-900">{formatEGP(financed)}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
              <p className="text-slate-500">{t('schedule_total')}</p>
              <p className="text-lg font-semibold text-slate-900">{formatEGP(scheduleTotal)}</p>
            </div>
            <div className={cn('rounded-lg border p-4 text-sm', balanced ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50')}>
              <p className="text-slate-500">{t('balance_check')}</p>
              <p className={cn('text-lg font-semibold', balanced ? 'text-emerald-700' : 'text-amber-700')}>
                {balanced ? t('balanced') : t('unbalanced')}
              </p>
            </div>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 text-start">#</th>
                  <th className="px-4 py-3 text-start">{t('due_date')}</th>
                  <th className="px-4 py-3 text-start">{t('amount')}</th>
                  <th className="px-4 py-3 text-start">{t('remaining')}</th>
                  <th className="px-4 py-3 text-start">{t('manual')}</th>
                </tr>
              </thead>
              <tbody>
                {schedule.map((row, index) => (
                  <tr key={row.installment_number} className="border-t border-slate-100">
                    <td className="px-4 py-3">{row.installment_number}</td>
                    <td className="px-4 py-3">{row.due_date}</td>
                    <td className="px-4 py-3">
                      <input
                        type="number"
                        min={0}
                        step="0.01"
                        className="input-field min-w-[9rem]"
                        value={row.due_amount}
                        onChange={(e) => updateAmountLocal(index, e.target.value)}
                        onBlur={() => commitAmount(index)}
                        onKeyDown={(e) => { if (e.key === 'Enter') commitAmount(index) }}
                      />
                    </td>
                    <td className="px-4 py-3">{formatEGP(row.remaining_balance ?? row.due_amount)}</td>
                    <td className="px-4 py-3">
                      {row.is_manual ? (
                        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">{t('manual')}</span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-500">{t('installment_manual_hint')}</p>
        </>
      )}
    </div>
  )
}
