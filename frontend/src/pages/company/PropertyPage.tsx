import { useTranslation } from 'react-i18next'
import { Building2, Home, Wrench, User, CheckCircle2, Clock, AlertCircle, Plus } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { StatCard } from '@/components/ui/StatCard'
import { Button } from '@/components/ui/Button'
import { useListData } from '@/hooks/useListData'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { MaintenanceFormModal } from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useState } from 'react'

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
  const modal = useCrudModal()
  const deleteMaint = useDeleteEntity('/property/maintenance', ['maintenance'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('maintenance', '/property/maintenance')

  const { data: summary } = useQuery({
    queryKey: ['property-summary'],
    queryFn: async () => (await api.get('/property/summary')).data,
  })

  return (
    <div>
      <PageHeader
        title={t('property')}
        subtitle={t('property_about')}
        icon={Building2}
        accentIndex={4}
        actions={
          <Button onClick={modal.openCreate}>
            <Plus className="me-2 h-4 w-4" />{t('add_maintenance')}
          </Button>
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
        <p className="mt-4 text-sm text-slate-600">{t('property_example')}</p>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title={t('total_requests')} value={formatInteger(summary?.total)} icon={Wrench} />
        <StatCard title={t('open_requests')} value={formatInteger(summary?.open)} icon={AlertCircle} color="bg-red-50 text-red-700" />
        <StatCard title={t('in_progress_requests')} value={formatInteger(summary?.in_progress)} icon={Clock} color="bg-amber-50 text-amber-700" />
        <StatCard title={t('completed_requests')} value={formatInteger(summary?.completed)} icon={CheckCircle2} color="bg-emerald-50 text-emerald-700" />
      </div>

      <DataTable
        title={t('maintenance_requests')}
        subtitle={t('property_help')}
        loading={isLoading}
        exportFilename="property"
        data={items}
        emptyActionLabel={t('add_maintenance')}
        onEmptyAction={modal.openCreate}
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
            onDelete={() => confirmDelete(t) && deleteMaint.mutate(row.id as number, { onSuccess: () => { refetch() } })}
          />
        )}
      />
      <MaintenanceFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}
