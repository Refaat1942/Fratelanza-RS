import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Building2, Home, Wrench, User, CheckCircle2, Clock, AlertCircle, Plus, Key } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { StatCard } from '@/components/ui/StatCard'
import { ReportLinkButton } from '@/components/ui/ReportLinkButton'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { useListData } from '@/hooks/useListData'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { MaintenanceFormModal } from '@/components/forms/ModuleFormModals'
import { useCustomersLookup, useUnitsLookup } from '@/hooks/useLookupData'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'maintenance' | 'handovers'

function useCrudModal() {
  const [open, setOpen] = useState(false)
  const [editRow, setEditRow] = useState<Record<string, unknown> | null>(null)
  return {
    open,
    editRow,
    openCreate: () => { setEditRow(null); setOpen(true) },
    openEdit: (row: Record<string, unknown>) => { setEditRow(row); setOpen(true) },
    close: () => { setOpen(false); setEditRow(null) },
  }
}

const STEPS = [
  { icon: Home, key: 'property_step_unit' },
  { icon: User, key: 'property_step_customer' },
  { icon: Wrench, key: 'property_step_fix' },
] as const

export function PropertyPage() {
  const { t } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const [tab, setTab] = useState<Tab>('maintenance')
  const modal = useCrudModal()
  const [handoverOpen, setHandoverOpen] = useState(false)
  const [handoverLoading, setHandoverLoading] = useState(false)
  const { data: units = [] } = useUnitsLookup()
  const { data: customers = [] } = useCustomersLookup()
  const [handoverForm, setHandoverForm] = useState({ unit_id: '', customer_id: '', handover_date: '', notes: '' })
  const deleteMaint = useDeleteEntity('/property/maintenance', ['maintenance'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('maintenance', '/property/maintenance')
  const { items: handovers, isLoading: handoversLoading, refetch: refetchHandovers } = useListData<Record<string, unknown>>('handovers', '/property/handovers')

  const { data: summary } = useQuery({
    queryKey: ['property-summary'],
    queryFn: async () => (await api.get('/property/summary')).data,
  })

  const submitHandover = async (e: React.FormEvent) => {
    e.preventDefault()
    setHandoverLoading(true)
    try {
      await api.post('/property/handovers', {
        unit_id: Number(handoverForm.unit_id),
        customer_id: Number(handoverForm.customer_id),
        handover_date: handoverForm.handover_date,
        notes: handoverForm.notes || undefined,
      })
      setHandoverOpen(false)
      setHandoverForm({ unit_id: '', customer_id: '', handover_date: '', notes: '' })
      refetchHandovers()
    } finally {
      setHandoverLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title={t('property')}
        subtitle={t('property_about')}
        icon={Building2}
        accentIndex={4}
        actions={
          <>
            <ReportLinkButton reportKey="property_maintenance" />
            {tab === 'maintenance' ? (
              <Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_maintenance')}</Button>
            ) : (
              <Button onClick={() => setHandoverOpen(true)}><Plus className="me-2 h-4 w-4" />{t('add_handover')}</Button>
            )}
          </>
        }
      />

      <div className="mb-6 rounded-xl border border-primary-200 bg-gradient-to-br from-primary-50 to-white p-5">
        <p className="mb-4 font-medium text-primary-900">{t('property_what_is_this')}</p>
        <div className="grid gap-4 md:grid-cols-3">
          {STEPS.map(({ icon: Icon, key }, i) => (
            <div key={key} className="flex gap-3 rounded-lg bg-white/80 p-4 ring-1 ring-primary-100">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-100 text-primary-700">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-primary-600">{t('step')} {i + 1}</p>
                <p className="text-sm text-slate-700">{t(key)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title={t('total_requests')} value={formatInteger(summary?.total)} icon={Wrench} />
        <StatCard title={t('open_requests')} value={formatInteger(summary?.open)} icon={AlertCircle} color="bg-red-50 text-red-700" />
        <StatCard title={t('in_progress_requests')} value={formatInteger(summary?.in_progress)} icon={Clock} color="bg-amber-50 text-amber-700" />
        <StatCard title={t('completed_requests')} value={formatInteger(summary?.completed)} icon={CheckCircle2} color="bg-emerald-50 text-emerald-700" />
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <button type="button" onClick={() => setTab('maintenance')} className={cn('rounded-lg px-3 py-1.5 text-sm font-medium', tab === 'maintenance' ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200')}>
          {t('maintenance_requests')}
        </button>
        <button type="button" onClick={() => setTab('handovers')} className={cn('flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium', tab === 'handovers' ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200')}>
          <Key className="h-4 w-4" />{t('handovers')}
        </button>
      </div>

      {tab === 'maintenance' && (
        <DataTable
          title={t('maintenance_requests')}
          subtitle={t('property_help')}
          loading={isLoading}
          exportFilename="property"
          data={items}
          columns={[
            { key: 'title', label: t('request') },
            { key: 'unit_code', label: t('units') },
            { key: 'customer_name', label: t('customers') },
            { key: 'priority', label: t('priority') },
            { key: 'status', label: t('status') },
          ]}
          rowActions={(row) => (
            <RowActions
              onEdit={() => modal.openEdit(row)}
              onDelete={() => confirmDelete(t) && deleteMaint.mutate(row.id as number, { onSuccess: () => refetch() })}
            />
          )}
        />
      )}

      {tab === 'handovers' && (
        <DataTable
          title={t('handovers')}
          loading={handoversLoading}
          exportFilename="handovers"
          data={handovers}
          columns={[
            { key: 'unit_code', label: t('units') },
            { key: 'customer_name', label: t('customers') },
            { key: 'handover_date', label: t('handover_date') },
            { key: 'status', label: t('status') },
            { key: 'notes', label: t('notes') },
          ]}
        />
      )}

      <MaintenanceFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />

      <Modal open={handoverOpen} onClose={() => setHandoverOpen(false)} title={t('add_handover')}>
        <form onSubmit={submitHandover} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">{t('units')}</label>
            <select className="input-field" value={handoverForm.unit_id} onChange={(e) => setHandoverForm({ ...handoverForm, unit_id: e.target.value })} required>
              <option value="">—</option>
              {units.map((u) => <option key={u.id} value={u.id}>{u.unit_code}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">{t('customers')}</label>
            <select className="input-field" value={handoverForm.customer_id} onChange={(e) => setHandoverForm({ ...handoverForm, customer_id: e.target.value })} required>
              <option value="">—</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.full_name_ar}</option>)}
            </select>
          </div>
          <Input label={t('handover_date')} type="date" value={handoverForm.handover_date} onChange={(e) => setHandoverForm({ ...handoverForm, handover_date: e.target.value })} required />
          <Input label={t('notes')} value={handoverForm.notes} onChange={(e) => setHandoverForm({ ...handoverForm, notes: e.target.value })} />
          <div className="flex gap-3">
            <Button type="submit" loading={handoverLoading}>{t('save')}</Button>
            <Button type="button" variant="secondary" onClick={() => setHandoverOpen(false)}>{t('cancel')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
