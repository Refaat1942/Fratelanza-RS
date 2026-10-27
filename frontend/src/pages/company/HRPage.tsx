import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Plus, Wallet, Calendar, Clock, Users, FileText } from 'lucide-react'
import { SortableTable } from '@/components/ui/SortableTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { exportRowsToExcel } from '@/lib/exportTable'
import api from '@/lib/api'
import { cn } from '@/lib/utils'
import { apiErrorMessage } from '@/lib/apiError'
import { DataTable } from '@/components/ui/DataTable'
import { ErrorNote } from '@/components/ui/FormFields'
import { usePermissionsStore } from '@/stores/permissionsStore'

type Tab = 'employees' | 'payroll' | 'payslips' | 'leaves' | 'attendance'

export function HRPage() {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('employees')
  const [empOpen, setEmpOpen] = useState(false)
  const [leaveOpen, setLeaveOpen] = useState(false)
  const [attOpen, setAttOpen] = useState(false)
  const [selectedRun, setSelectedRun] = useState<number | null>(null)
  const [payrollError, setPayrollError] = useState('')
  const perms = usePermissionsStore()
  const canPaySalaries = perms.can('hr', 'collect') && perms.sees('salaries')
  const [payRow, setPayRow] = useState<Record<string, unknown> | null>(null)
  const [payForm, setPayForm] = useState({ amount: '', paid_on: '' })
  const [payError, setPayError] = useState<string | null>(null)
  const [payBusy, setPayBusy] = useState(false)
  const paySalary = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!payRow) return
    setPayBusy(true); setPayError(null)
    try {
      await api.post(`/hr/payslips/${payRow.id}/payments`, { amount: Number(payForm.amount), paid_on: payForm.paid_on })
      setPayRow(null)
      qc.invalidateQueries({ queryKey: ['hr-all-payslips'] })
      qc.invalidateQueries({ queryKey: ['hr-payslips'] })
    } catch (err) {
      setPayError(apiErrorMessage(err, t))
    } finally {
      setPayBusy(false)
    }
  }
  const [form, setForm] = useState({
    employee_code: '', full_name_ar: '', full_name_en: '', department: '', position: '', salary: '', hire_date: '',
  })
  const [leaveForm, setLeaveForm] = useState({ employee_id: '', leave_type: 'annual', start_date: '', end_date: '', reason: '' })
  const [attForm, setAttForm] = useState({ employee_id: '', date: new Date().toISOString().slice(0, 10), check_in: '09:00', check_out: '17:00' })

  const { data: employees = [], isLoading: empLoading } = useQuery({
    queryKey: ['hr-employees'],
    queryFn: async () => (await api.get('/hr/employees')).data,
  })

  const { data: payroll = [], isLoading: payLoading } = useQuery({
    queryKey: ['hr-payroll'],
    queryFn: async () => (await api.get('/hr/payroll')).data,
  })

  const { data: payslips = [] } = useQuery({
    queryKey: ['hr-payslips', selectedRun],
    queryFn: async () => (await api.get(`/hr/payroll/${selectedRun}/payslips`)).data,
    enabled: !!selectedRun,
  })

  const { data: leaves = [], isLoading: leaveLoading } = useQuery({
    queryKey: ['hr-leaves'],
    queryFn: async () => (await api.get('/hr/leaves')).data,
    enabled: tab === 'leaves',
  })

  const { data: attendance = [], isLoading: attLoading } = useQuery({
    queryKey: ['hr-attendance'],
    queryFn: async () => (await api.get('/hr/attendance')).data,
    enabled: tab === 'attendance',
  })

  const generatePayroll = useMutation({
    mutationFn: async () => {
      const month = new Date().toISOString().slice(0, 7)
      return api.post('/hr/payroll/generate', null, { params: { period_month: month } })
    },
    onSuccess: (res) => {
      setPayrollError('')
      setSelectedRun(res.data.id)
      qc.invalidateQueries({ queryKey: ['hr-payroll'] })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      setPayrollError(err.response?.data?.detail || t('payroll_error'))
    },
  })

  const approveLeave = useMutation({
    mutationFn: (id: number) => api.post(`/hr/leaves/${id}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hr-leaves'] }),
  })

  const deleteEmployee = useMutation({
    mutationFn: (id: number) => api.delete(`/hr/employees/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hr-employees'] }),
  })

  const deleteLeave = useMutation({
    mutationFn: (id: number) => api.delete(`/hr/leaves/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hr-leaves'] }),
  })

  const deleteAttendance = useMutation({
    mutationFn: (id: number) => api.delete(`/hr/attendance/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hr-attendance'] }),
  })

  const { data: allPayslips = [], isLoading: payslipsLoading } = useQuery({
    queryKey: ['hr-all-payslips'],
    queryFn: async () => (await api.get('/hr/payslips')).data,
    enabled: tab === 'payslips',
  })

  const tabs: { key: Tab; label: string; icon: typeof Users }[] = [
    { key: 'employees', label: t('employees'), icon: Users },
    { key: 'payroll', label: t('payroll'), icon: Wallet },
    { key: 'payslips', label: t('payslips'), icon: FileText },
    { key: 'leaves', label: t('leaves'), icon: Calendar },
    { key: 'attendance', label: t('attendance'), icon: Clock },
  ]

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('hr')}</h1>
          <p className="text-sm text-slate-500">{t('hr_help')}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {tab === 'employees' && <Button onClick={() => setEmpOpen(true)}><Plus className="me-2 h-4 w-4" />{t('add_employee')}</Button>}
          {tab === 'leaves' && <Button onClick={() => setLeaveOpen(true)}><Plus className="me-2 h-4 w-4" />{t('request_leave')}</Button>}
          {tab === 'attendance' && <Button onClick={() => setAttOpen(true)}><Plus className="me-2 h-4 w-4" />{t('record_attendance')}</Button>}
          {tab === 'payroll' && (
            <Button onClick={() => generatePayroll.mutate()} loading={generatePayroll.isPending}>
              <Wallet className="me-2 h-4 w-4" />{t('generate_payroll')}
            </Button>
          )}
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setTab(key)} className={cn(
            'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium',
            tab === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
          )}>
            <Icon className="h-4 w-4" />{label}
          </button>
        ))}
      </div>

      {tab === 'employees' && (
        employees.length === 0 && !empLoading ? (
          <EmptyState icon={<Users className="h-10 w-10" />} title={t('no_employees')} description={t('no_employees_help')} actionLabel={t('add_employee')} onAction={() => setEmpOpen(true)} />
        ) : (
          <div className="space-y-2">
            {employees.map((e: Record<string, unknown>) => (
              <div key={e.id as number} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4">
                <div>
                  <p className="font-medium">{e.full_name_en as string} <span className="text-slate-400">({e.employee_code as string})</span></p>
                  <p className="text-xs text-slate-500">{e.department as string} · {formatEGP(e.salary as number)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => window.confirm(t('confirm_delete')) && deleteEmployee.mutate(e.id as number)}
                  className="text-sm text-red-600 hover:underline"
                >
                  {t('delete')}
                </button>
              </div>
            ))}
          </div>
        )
      )}

      {tab === 'payroll' && (
        <>
          {payrollError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{payrollError}</p>}
          {payroll.length === 0 && !payLoading ? (
            <EmptyState icon={<Wallet className="h-10 w-10" />} title={t('no_payroll')} description={t('no_payroll_help')} actionLabel={t('generate_payroll')} onAction={() => generatePayroll.mutate()} />
          ) : (
            <>
              <SortableTable columns={[
                { key: 'period_month', label_en: 'Month', label_ar: 'الشهر' },
                { key: 'total_gross', label_en: 'Gross', label_ar: 'الإجمالي' },
                { key: 'total_net', label_en: 'Net', label_ar: 'الصافي' },
                { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
              ]} rows={payroll.map((p: Record<string, unknown>) => ({
                ...p,
                total_gross: formatEGP(p.total_gross as number),
                total_net: formatEGP(p.total_net as number),
              }))} loading={payLoading} onExport={() => exportRowsToExcel(payroll, 'payroll')} />
              <div className="mt-4 flex flex-wrap gap-2">
                {payroll.map((p: { id: number; period_month: string }) => (
                  <button key={p.id} onClick={() => setSelectedRun(p.id)} className={cn(
                    'rounded-lg px-3 py-1.5 text-sm',
                    selectedRun === p.id ? 'bg-primary-100 text-primary-800' : 'bg-slate-100 text-slate-600',
                  )}>{t('view_payslips')} — {p.period_month}</button>
                ))}
              </div>
              {selectedRun && payslips.length > 0 && (
                <div className="mt-4">
                  <SortableTable columns={[
                    { key: 'employee_name', label_en: 'Employee', label_ar: 'الموظف' },
                    { key: 'basic_salary_egp', label_en: 'Basic', label_ar: 'الأساسي' },
                    { key: 'social_insurance_egp', label_en: 'Insurance 11%', label_ar: 'التأمينات' },
                    { key: 'net_salary_egp', label_en: 'Net', label_ar: 'الصافي' },
                  ]} rows={payslips.map((s: Record<string, unknown>) => ({
                    ...s,
                    basic_salary_egp: formatEGP(s.basic_salary_egp as number),
                    social_insurance_egp: formatEGP(s.social_insurance_egp as number),
                    net_salary_egp: formatEGP(s.net_salary_egp as number),
                  }))} onExport={() => exportRowsToExcel(payslips, 'payslips')} />
                </div>
              )}
            </>
          )}
        </>
      )}

      {tab === 'payslips' && (
        allPayslips.length === 0 && !payslipsLoading ? (
          <EmptyState icon={<FileText className="h-10 w-10" />} title={t('no_payslips')} description={t('no_payslips_help')} actionLabel={t('generate_payroll')} onAction={() => generatePayroll.mutate()} />
        ) : (
          <>
            <DataTable
              title={t('payslips')}
              subtitle={t('re.payroll.subtitle')}
              loading={payslipsLoading}
              data={allPayslips}
              exportFilename="payslips"
              columns={[
                { key: 'period_month', label: t('re.payroll.month') },
                { key: 'employee_code', label: t('re.fields.code') },
                { key: 'employee_name', label: t('re.payroll.employee') },
                { key: 'basic_salary', label: t('re.payroll.basic'), render: (r) => formatEGP(r.basic_salary as number) },
                { key: 'social_insurance', label: t('re.payroll.insurance'), render: (r) => formatEGP(r.social_insurance as number) },
                { key: 'net_salary', label: t('re.payroll.net'), render: (r) => formatEGP(r.net_salary as number) },
                { key: 'paid_amount', label: t('re.fields.paid'), render: (r) => formatEGP(r.paid_amount as number) },
                { key: 'remaining', label: t('re.fields.remaining'), render: (r) => formatEGP(Number(r.net_salary ?? 0) - Number(r.paid_amount ?? 0)) },
                { key: 'status', label: t('status'), render: (r) => t(`re.payroll.status_${r.status}`, { defaultValue: String(r.status) }) },
              ]}
              rowActions={(row) => (canPaySalaries && Number(row.net_salary ?? 0) - Number(row.paid_amount ?? 0) > 0 ? (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => {
                  setPayError(null)
                  setPayForm({ amount: String(Number(row.net_salary) - Number(row.paid_amount ?? 0)), paid_on: new Date().toISOString().slice(0, 10) })
                  setPayRow(row)
                }}>
                  <Wallet className="me-1 h-3.5 w-3.5" />{t('re.payroll.pay')}
                </Button>
              ) : null)}
            />
            <Modal open={!!payRow} onClose={() => setPayRow(null)} title={t('re.payroll.pay')}>
              <form onSubmit={paySalary} className="space-y-4">
                <ErrorNote message={payError} />
                <p className="text-sm text-slate-600">{String(payRow?.employee_name ?? '')} — {String(payRow?.period_month ?? '')}</p>
                <Input type="number" min="0.01" step="0.01" label={t('re.fields.amount')} value={payForm.amount} onChange={(e) => setPayForm({ ...payForm, amount: e.target.value })} required />
                <Input type="date" label={t('re.fields.date')} value={payForm.paid_on} onChange={(e) => setPayForm({ ...payForm, paid_on: e.target.value })} required />
                <div className="flex gap-3"><Button type="submit" loading={payBusy}>{t('re.confirm')}</Button><Button type="button" variant="secondary" onClick={() => setPayRow(null)}>{t('cancel')}</Button></div>
              </form>
            </Modal>
          </>
        )
      )}

      {tab === 'leaves' && (
        leaves.length === 0 && !leaveLoading ? (
          <EmptyState icon={<Calendar className="h-10 w-10" />} title={t('no_leaves')} description={t('no_leaves_help')} actionLabel={t('request_leave')} onAction={() => setLeaveOpen(true)} />
        ) : (
          <div className="space-y-2">
            {leaves.map((l: Record<string, unknown>) => (
              <div key={l.id as number} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4">
                <div>
                  <p className="font-medium">{l.employee_name as string} — {l.leave_type as string}</p>
                  <p className="text-xs text-slate-500">{l.start_date as string} → {l.end_date as string} · {l.status as string}</p>
                </div>
                <div className="flex gap-2">
                  {l.status === 'pending' && (
                    <Button variant="secondary" onClick={() => approveLeave.mutate(l.id as number)}>{t('approve')}</Button>
                  )}
                  <button
                    type="button"
                    onClick={() => window.confirm(t('confirm_delete')) && deleteLeave.mutate(l.id as number)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    {t('delete')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {tab === 'attendance' && (
        attendance.length === 0 && !attLoading ? (
          <EmptyState icon={<Clock className="h-10 w-10" />} title={t('no_attendance')} description={t('no_attendance_help')} actionLabel={t('record_attendance')} onAction={() => setAttOpen(true)} />
        ) : (
          <SortableTable columns={[
            { key: 'employee_name', label_en: 'Employee', label_ar: 'الموظف' },
            { key: 'date', label_en: 'Date', label_ar: 'التاريخ' },
            { key: 'check_in', label_en: 'In', label_ar: 'حضور' },
            { key: 'check_out', label_en: 'Out', label_ar: 'انصراف' },
            { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
            { key: 'actions', label_en: 'Actions', label_ar: 'إجراءات' },
          ]} rows={attendance.map((a: Record<string, unknown>) => ({
            ...a,
            actions: (
              <button
                type="button"
                onClick={() => window.confirm(t('confirm_delete')) && deleteAttendance.mutate(a.id as number)}
                className="text-sm text-red-600 hover:underline"
              >
                {t('delete')}
              </button>
            ),
          }))} loading={attLoading} onExport={() => exportRowsToExcel(attendance, 'attendance')} />
        )
      )}

      <Modal open={empOpen} onClose={() => setEmpOpen(false)} title={t('add_employee')}>
        <form onSubmit={async (e) => {
          e.preventDefault()
          await api.post('/hr/employees', { ...form, salary: Number(form.salary) || 0 })
          setEmpOpen(false)
          qc.invalidateQueries({ queryKey: ['hr-employees'] })
        }} className="space-y-4">
          <Input label={t('employee_code')} value={form.employee_code} onChange={(e) => setForm({ ...form, employee_code: e.target.value })} required />
          <Input label={t('name_ar')} value={form.full_name_ar} onChange={(e) => setForm({ ...form, full_name_ar: e.target.value })} required />
          <Input label={t('name_en')} value={form.full_name_en} onChange={(e) => setForm({ ...form, full_name_en: e.target.value })} required />
          <Input label={t('department')} value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
          <Input label={t('salary_egp')} type="number" value={form.salary} onChange={(e) => setForm({ ...form, salary: e.target.value })} />
          <Button type="submit">{t('save')}</Button>
        </form>
      </Modal>

      <Modal open={leaveOpen} onClose={() => setLeaveOpen(false)} title={t('request_leave')}>
        <form onSubmit={async (e) => {
          e.preventDefault()
          await api.post('/hr/leaves', { ...leaveForm, employee_id: Number(leaveForm.employee_id) })
          setLeaveOpen(false)
          qc.invalidateQueries({ queryKey: ['hr-leaves'] })
        }} className="space-y-4">
          <select className="input-field" value={leaveForm.employee_id} onChange={(e) => setLeaveForm({ ...leaveForm, employee_id: e.target.value })} required>
            <option value="">{t('select_employee')}</option>
            {employees.map((e: { id: number; full_name_en: string }) => <option key={e.id} value={e.id}>{e.full_name_en}</option>)}
          </select>
          <Input label={t('start_date')} type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} required />
          <Input label={t('end_date')} type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} required />
          <Button type="submit">{t('save')}</Button>
        </form>
      </Modal>

      <Modal open={attOpen} onClose={() => setAttOpen(false)} title={t('record_attendance')}>
        <form onSubmit={async (e) => {
          e.preventDefault()
          await api.post('/hr/attendance', { ...attForm, employee_id: Number(attForm.employee_id) })
          setAttOpen(false)
          qc.invalidateQueries({ queryKey: ['hr-attendance'] })
        }} className="space-y-4">
          <select className="input-field" value={attForm.employee_id} onChange={(e) => setAttForm({ ...attForm, employee_id: e.target.value })} required>
            <option value="">{t('select_employee')}</option>
            {employees.map((e: { id: number; full_name_en: string }) => <option key={e.id} value={e.id}>{e.full_name_en}</option>)}
          </select>
          <Input label={t('due_date')} type="date" value={attForm.date} onChange={(e) => setAttForm({ ...attForm, date: e.target.value })} required />
          <div className="grid grid-cols-2 gap-4">
            <Input label={t('check_in')} type="time" value={attForm.check_in} onChange={(e) => setAttForm({ ...attForm, check_in: e.target.value })} />
            <Input label={t('check_out')} type="time" value={attForm.check_out} onChange={(e) => setAttForm({ ...attForm, check_out: e.target.value })} />
          </div>
          <Button type="submit">{t('save')}</Button>
        </form>
      </Modal>
    </div>
  )
}
