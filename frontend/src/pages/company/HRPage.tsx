import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Plus, Wallet } from 'lucide-react'
import { SortableTable } from '@/components/ui/SortableTable'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { formatEGP } from '@/lib/currency'
import { exportRowsToExcel } from '@/lib/exportTable'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'employees' | 'payroll' | 'leaves' | 'attendance'

export function HRPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('employees')
  const [empOpen, setEmpOpen] = useState(false)
  const [form, setForm] = useState({
    employee_code: '', full_name_ar: '', full_name_en: '', department: '', position: '', salary: '', hire_date: '',
  })

  const { data: employees = [], isLoading: empLoading } = useQuery({
    queryKey: ['hr-employees'],
    queryFn: async () => (await api.get('/hr/employees')).data,
    enabled: tab === 'employees',
  })

  const { data: payroll = [], isLoading: payLoading } = useQuery({
    queryKey: ['hr-payroll'],
    queryFn: async () => (await api.get('/hr/payroll')).data,
    enabled: tab === 'payroll',
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hr-payroll'] }),
  })

  const createEmployee = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.post('/hr/employees', { ...form, salary: Number(form.salary) || 0 })
    setEmpOpen(false)
    qc.invalidateQueries({ queryKey: ['hr-employees'] })
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'employees', label: t('employees') },
    { key: 'payroll', label: t('payroll') },
    { key: 'leaves', label: t('leaves') },
    { key: 'attendance', label: t('attendance') },
  ]

  const empCols = [
    { key: 'employee_code', label_en: 'Code', label_ar: 'الكود' },
    { key: 'full_name_en', label_en: 'Name', label_ar: 'الاسم' },
    { key: 'department', label_en: 'Department', label_ar: 'القسم' },
    { key: 'position', label_en: 'Position', label_ar: 'الوظيفة' },
    { key: 'salary', label_en: 'Salary (EGP)', label_ar: 'الراتب (ج.م)' },
    { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
  ]

  const empRows = employees.map((e: Record<string, unknown>) => ({
    ...e,
    salary: formatEGP(e.salary as number),
    status: e.is_active ? 'active' : 'inactive',
  }))

  const payCols = [
    { key: 'period_month', label_en: 'Period', label_ar: 'الفترة' },
    { key: 'total_gross', label_en: 'Gross (EGP)', label_ar: 'الإجمالي' },
    { key: 'total_deductions', label_en: 'Deductions', label_ar: 'الخصومات' },
    { key: 'total_net', label_en: 'Net (EGP)', label_ar: 'الصافي' },
    { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
  ]

  const payRows = payroll.map((p: Record<string, unknown>) => ({
    ...p,
    total_gross: formatEGP(p.total_gross as number),
    total_deductions: formatEGP(p.total_deductions as number),
    total_net: formatEGP(p.total_net as number),
  }))

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('hr')}</h1>
          <p className="text-sm text-slate-500">{t('hr_subtitle')}</p>
        </div>
        {tab === 'employees' && (
          <Button onClick={() => setEmpOpen(true)}><Plus className="me-2 h-4 w-4" />{t('add_employee')}</Button>
        )}
        {tab === 'payroll' && (
          <Button onClick={() => generatePayroll.mutate()} loading={generatePayroll.isPending}>
            <Wallet className="me-2 h-4 w-4" />{t('generate_payroll')}
          </Button>
        )}
      </div>

      <div className="mb-4 flex gap-2">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={cn(
              'rounded-lg px-4 py-2 text-sm font-medium',
              tab === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'employees' && (
        <SortableTable
          columns={empCols}
          rows={empRows}
          loading={empLoading}
          onExport={() => exportRowsToExcel(employees, 'employees')}
        />
      )}
      {tab === 'payroll' && (
        <SortableTable
          columns={payCols}
          rows={payRows}
          loading={payLoading}
          onExport={() => exportRowsToExcel(payroll, 'payroll')}
        />
      )}
      {tab === 'leaves' && (
        <SortableTable
          columns={[
            { key: 'employee_name', label_en: 'Employee', label_ar: 'الموظف' },
            { key: 'leave_type', label_en: 'Type', label_ar: 'النوع' },
            { key: 'start_date', label_en: 'From', label_ar: 'من' },
            { key: 'end_date', label_en: 'To', label_ar: 'إلى' },
            { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
          ]}
          rows={leaves}
          loading={leaveLoading}
          onExport={() => exportRowsToExcel(leaves, 'leaves')}
        />
      )}
      {tab === 'attendance' && (
        <SortableTable
          columns={[
            { key: 'employee_name', label_en: 'Employee', label_ar: 'الموظف' },
            { key: 'date', label_en: 'Date', label_ar: 'التاريخ' },
            { key: 'check_in', label_en: 'Check In', label_ar: 'الحضور' },
            { key: 'check_out', label_en: 'Check Out', label_ar: 'الانصراف' },
            { key: 'status', label_en: 'Status', label_ar: 'الحالة' },
          ]}
          rows={attendance}
          loading={attLoading}
          onExport={() => exportRowsToExcel(attendance, 'attendance')}
        />
      )}

      <Modal open={empOpen} onClose={() => setEmpOpen(false)} title={t('add_employee')}>
        <form onSubmit={createEmployee} className="space-y-4">
          <Input label={t('employee_code')} value={form.employee_code} onChange={(e) => setForm({ ...form, employee_code: e.target.value })} required />
          <Input label={t('name_ar')} value={form.full_name_ar} onChange={(e) => setForm({ ...form, full_name_ar: e.target.value })} required />
          <Input label={t('name_en')} value={form.full_name_en} onChange={(e) => setForm({ ...form, full_name_en: e.target.value })} required />
          <Input label={t('department')} value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
          <Input label={t('position')} value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })} />
          <Input label={t('salary_egp')} type="number" value={form.salary} onChange={(e) => setForm({ ...form, salary: e.target.value })} />
          <div className="flex gap-3"><Button type="submit">{t('save')}</Button><Button type="button" variant="secondary" onClick={() => setEmpOpen(false)}>{t('cancel')}</Button></div>
        </form>
      </Modal>
    </div>
  )
}
