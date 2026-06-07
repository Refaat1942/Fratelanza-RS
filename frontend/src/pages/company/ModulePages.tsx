import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, CheckCircle, FileText, CreditCard, XCircle } from 'lucide-react'
import { ReportLinkButton } from '@/components/ui/ReportLinkButton'
import { PageHeader } from '@/components/ui/PageHeader'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { useListData } from '@/hooks/useListData'
import { useModuleList } from '@/hooks/useModuleList'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { Button } from '@/components/ui/Button'
import {
  ReservationFormModal, ContractFormModal,
  PaymentFormModal,
} from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'

function EntityLink({ to, label }: { to: string; label: string }) {
  return <Link to={to} className="font-medium text-primary-600 hover:underline">{label}</Link>
}

function useCrudModal() {
  const [open, setOpen] = useState(false)
  const [editRow, setEditRow] = useState<Record<string, unknown> | null>(null)
  const openCreate = () => { setEditRow(null); setOpen(true) }
  const openEdit = (row: Record<string, unknown>) => { setEditRow(row); setOpen(true) }
  const close = () => { setOpen(false); setEditRow(null) }
  return { open, editRow, openCreate, openEdit, close }
}

export function ReservationsPage() {
  const { t } = useTranslation()
  const modal = useCrudModal()
  const [contractOpen, setContractOpen] = useState(false)
  const [selectedRes, setSelectedRes] = useState<Record<string, unknown> | null>(null)
  const qc = useQueryClient()
  const deleteRes = useDeleteEntity('/reservations', ['reservations'])
  const approve = useMutation({
    mutationFn: (id: number) => api.post(`/reservations/${id}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  })
  const cancelRes = useMutation({
    mutationFn: (id: number) => api.put(`/reservations/${id}`, { status: 'cancelled' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  })
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('reservations', '/reservations')

  return (
    <div>
      <PageHeader title={t('reservations')} subtitle={t('reservations_help')} actions={<ReportLinkButton reportKey="reservations" />} />
      <DataTable
        title={t('reservations')}
        loading={isLoading}
        exportFilename="reservations"
        data={items}
        actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_reservation')}</Button>}
        emptyActionLabel={t('add_reservation')}
        onEmptyAction={modal.openCreate}
        columns={[
          { key: 'reservation_number', label: '#' },
          { key: 'customer_name', label: t('customers'), render: (row) => <EntityLink to="/customers" label={String(row.customer_name ?? row.customer_id)} /> },
          { key: 'unit_code', label: t('units'), render: (row) => <EntityLink to="/projects" label={String(row.unit_code ?? row.unit_id)} /> },
          { key: 'deposit_amount', label: t('deposit') },
          { key: 'status', label: t('status') },
          { key: 'expiry_date', label: t('expiry_date') },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deleteRes.mutate(row.id as number, { onSuccess: () => { refetch() } })}
            extra={
              <>
                {row.status === 'pending_approval' && (
                  <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => approve.mutate(row.id as number)} title={t('approve')}>
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                  </Button>
                )}
                {row.status === 'approved' && (
                  <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => { setSelectedRes(row); setContractOpen(true) }} title={t('convert_to_contract')}>
                    <FileText className="h-4 w-4 text-primary-600" />
                  </Button>
                )}
                {row.status !== 'cancelled' && row.status !== 'converted' && (
                  <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => cancelRes.mutate(row.id as number)} title={t('cancel_reservation')}>
                    <XCircle className="h-4 w-4 text-red-600" />
                  </Button>
                )}
              </>
            }
          />
        )}
      />
      <ReservationFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
      <ContractFormModal open={contractOpen} onClose={() => { setContractOpen(false); setSelectedRes(null); refetch() }}
        editRow={selectedRes ? { customer_id: selectedRes.customer_id, unit_id: selectedRes.unit_id, reservation_id: selectedRes.id } : null} />
    </div>
  )
}

export function ContractsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { formatEGP } = useFormatNumber()
  const modal = useCrudModal()
  const deleteContract = useDeleteEntity('/contracts', ['contracts'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('contracts', '/contracts')

  return (
    <div>
      <PageHeader title={t('contracts')} actions={<ReportLinkButton reportKey="sales_register" />} />
      <DataTable
        title={t('contracts')}
        loading={isLoading}
        exportFilename="contracts"
        data={items}
        actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_contract')}</Button>}
        emptyActionLabel={t('add_contract')}
        onEmptyAction={modal.openCreate}
        columns={[
          { key: 'contract_number', label: '#' },
          { key: 'customer_name', label: t('customers'), render: (row) => <EntityLink to="/customers" label={String(row.customer_name ?? row.customer_id)} /> },
          { key: 'unit_code', label: t('units'), render: (row) => <EntityLink to="/projects" label={String(row.unit_code ?? row.unit_id)} /> },
          { key: 'total_price', label: t('total_sales'), render: (row) => formatEGP(row.total_price as number) },
          { key: 'status', label: t('status') },
          { key: 'contract_date', label: 'Date' },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deleteContract.mutate(row.id as number, { onSuccess: () => { refetch() } })}
            extra={
              <Button variant="ghost" className="!px-2 !py-1.5" title={t('collections')} onClick={() => navigate('/collections')}>
                <CreditCard className="h-4 w-4 text-primary-600" />
              </Button>
            }
          />
        )}
      />
      <ContractFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}

export function CollectionsPage() {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [installment, setInstallment] = useState<Record<string, unknown> | null>(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('installments', '/collections/installments')

  const filteredItems = useMemo(() => {
    if (statusFilter === 'all') return items
    if (statusFilter === 'overdue') return items.filter((r) => r.status === 'overdue' || (Number(r.remaining_balance) > 0 && r.status !== 'paid'))
    return items.filter((r) => r.status === statusFilter)
  }, [items, statusFilter])

  return (
    <div>
      <PageHeader title={t('collections')} subtitle={t('collections_help')} actions={<ReportLinkButton reportKey="collections_overdue" />} />
      <div className="mb-4 flex flex-wrap gap-2">
        {['all', 'due', 'overdue', 'partial', 'paid'].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatusFilter(s)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium capitalize ${statusFilter === s ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200'}`}
          >
            {s === 'all' ? t('all') : s}
          </button>
        ))}
      </div>
      <DataTable
        title={t('collections')}
        loading={isLoading}
        exportFilename="collections"
        data={filteredItems}
        columns={[
          { key: 'contract_number', label: t('contracts'), render: (row) => <EntityLink to="/contracts" label={String(row.contract_number)} /> },
          { key: 'customer_name', label: t('customers'), render: (row) => <EntityLink to="/customers" label={String(row.customer_name)} /> },
          { key: 'unit_code', label: t('units') },
          { key: 'installment_number', label: '#' },
          { key: 'due_date', label: 'Due' },
          { key: 'due_amount', label: 'Amount (EGP)', render: (row) => formatEGP(row.due_amount as number) },
          { key: 'paid_amount', label: t('paid'), render: (row) => formatEGP(row.paid_amount as number) },
          { key: 'remaining_balance', label: t('remaining'), render: (row) => formatEGP(row.remaining_balance as number) },
          { key: 'status', label: t('status') },
        ]}
        rowActions={(row) => (
          <RowActions
            extra={
              row.status !== 'paid' ? (
                <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => { setInstallment(row); setPaymentOpen(true) }} title={t('record_payment')}>
                  <CreditCard className="h-4 w-4 text-emerald-600" />
                </Button>
              ) : undefined
            }
          />
        )}
      />
      <PaymentFormModal open={paymentOpen} onClose={() => { setPaymentOpen(false); setInstallment(null); refetch() }} installment={installment} />
    </div>
  )
}

export function AuditLogsPage() {
  const { t } = useTranslation()
  const { data, isLoading } = useModuleList<{ items: Record<string, unknown>[] }>('audit-logs', '/super-admin/audit-logs')
  return (
    <DataTable
      title={t('audit_logs')}
      loading={isLoading}
      data={data?.items ?? []}
      columns={[
        { key: 'action', label: 'Action' },
        { key: 'module', label: 'Module' },
        { key: 'user_id', label: 'User' },
        { key: 'created_at', label: 'Date' },
      ]}
    />
  )
}

export function SubscriptionsPage() {
  const { t } = useTranslation()
  const { data, isLoading } = useModuleList<Record<string, unknown>[]>('plans', '/super-admin/subscription-plans')
  return (
    <DataTable
      title={t('subscriptions')}
      loading={isLoading}
      data={Array.isArray(data) ? data : []}
      columns={[
        { key: 'name_ar', label: 'Plan' },
        { key: 'code', label: 'Code' },
      ]}
    />
  )
}

export function SettingsPage() {
  const { t } = useTranslation()
  const { data, isLoading } = useModuleList<Record<string, unknown>[]>('settings', '/super-admin/settings')
  return (
    <DataTable
      title={t('settings')}
      loading={isLoading}
      data={Array.isArray(data) ? data : []}
      columns={[
        { key: 'key', label: 'Key' },
        { key: 'value', label: 'Value' },
      ]}
      actions={
        <Button variant="secondary" onClick={async () => {
          await api.post('/super-admin/backup')
          alert('Backup requested')
        }}>
          Backup DB
        </Button>
      }
    />
  )
}
