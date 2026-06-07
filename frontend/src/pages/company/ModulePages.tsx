import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, CheckCircle, FileText, CreditCard, Sliders, KeyRound, Power } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { useListData } from '@/hooks/useListData'
import { useModuleList } from '@/hooks/useModuleList'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { Button } from '@/components/ui/Button'
import { UserFormModal } from '@/components/forms/UserFormModal'
import { UserEditModal, type AdminUser } from '@/components/forms/UserEditModal'
import { ResetPasswordModal } from '@/components/forms/ResetPasswordModal'
import { UserFeaturesModal } from '@/components/forms/UserFeaturesModal'
import {
  ReservationFormModal, ContractFormModal,
  PaymentFormModal, BrokerFormModal,
  VendorFormModal, ConstructionPhaseFormModal,
  TicketFormModal,
} from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { roleLabel } from '@/constants/roles'

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
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('reservations', '/reservations')

  return (
    <div>
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
  const { formatEGP } = useFormatNumber()
  const modal = useCrudModal()
  const deleteContract = useDeleteEntity('/contracts', ['contracts'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('contracts', '/contracts')

  return (
    <div>
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
              <Button variant="ghost" className="!px-2 !py-1.5" title={t('collections')} onClick={() => { window.location.href = '/collections' }}>
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
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('installments', '/collections/installments')

  return (
    <div>
      <DataTable
        title={t('collections')}
        subtitle={t('collections_help')}
        loading={isLoading}
        exportFilename="collections"
        data={items}
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

export function BrokersPage() {
  const { t, i18n } = useTranslation()
  const modal = useCrudModal()
  const deleteBroker = useDeleteEntity('/brokers', ['brokers'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('brokers', '/brokers')

  return (
    <div>
      <DataTable
        title={t('brokers')}
        loading={isLoading}
        exportFilename="brokers"
        data={items}
        actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_broker')}</Button>}
        emptyActionLabel={t('add_broker')}
        onEmptyAction={modal.openCreate}
        columns={[
          { key: 'id', label: '#' },
          { key: 'name', label: t('brokers'), render: (row) => String(i18n.language === 'ar' ? row.name_ar : row.name_en) },
          { key: 'mobile', label: 'Mobile' },
          { key: 'commission_rate', label: 'Rate %' },
          { key: 'rank_score', label: 'Rank' },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deleteBroker.mutate(row.id as number, { onSuccess: () => { refetch() } })}
          />
        )}
      />
      <BrokerFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}

export function ConstructionPage() {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const modal = useCrudModal()
  const deletePhase = useDeleteEntity('/construction/phases', ['phases'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('phases', '/construction/phases')

  return (
    <div>
      <DataTable
        title={t('construction')}
        loading={isLoading}
        exportFilename="construction"
        data={items}
        actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_phase')}</Button>}
        emptyActionLabel={t('add_phase')}
        onEmptyAction={modal.openCreate}
        columns={[
          { key: 'project_name', label: t('projects'), render: (row) => <EntityLink to="/projects" label={String(row.project_name)} /> },
          { key: 'name_ar', label: t('construction') },
          { key: 'progress_percent', label: 'Progress %' },
          { key: 'planned_cost', label: 'Planned', render: (row) => formatEGP(row.planned_cost as number) },
          { key: 'actual_cost', label: 'Actual', render: (row) => formatEGP(row.actual_cost as number) },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deletePhase.mutate(row.id as number, { onSuccess: () => { refetch() } })}
          />
        )}
      />
      <ConstructionPhaseFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}

export function ProcurementPage() {
  const { t } = useTranslation()
  const modal = useCrudModal()
  const deleteVendor = useDeleteEntity('/procurement/vendors', ['vendors'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('vendors', '/procurement/vendors')

  return (
    <div>
      <DataTable
        title={t('procurement')}
        loading={isLoading}
        exportFilename="procurement"
        data={items}
        actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_vendor')}</Button>}
        emptyActionLabel={t('add_vendor')}
        onEmptyAction={modal.openCreate}
        columns={[
          { key: 'name_ar', label: 'Vendor' },
          { key: 'contact_person', label: 'Contact' },
          { key: 'phone', label: 'Phone' },
          { key: 'rating', label: 'Rating' },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deleteVendor.mutate(row.id as number, { onSuccess: () => { refetch() } })}
          />
        )}
      />
      <VendorFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}

export function CustomerServicePage() {
  const { t } = useTranslation()
  const modal = useCrudModal()
  const deleteTicket = useDeleteEntity('/tickets', ['tickets'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('tickets', '/tickets')
  return (
    <div>
      <DataTable
        title={t('customer_service')}
        subtitle={t('customer_service_help')}
        loading={isLoading}
        exportFilename="tickets"
        data={items}
        actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_ticket')}</Button>}
        emptyActionLabel={t('add_ticket')}
        onEmptyAction={modal.openCreate}
        columns={[
          { key: 'ticket_number', label: '#' },
          { key: 'subject', label: 'Subject' },
          { key: 'customer_name', label: t('customers') },
          { key: 'category', label: 'Category' },
          { key: 'priority', label: 'Priority' },
          { key: 'status', label: t('status') },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deleteTicket.mutate(row.id as number, { onSuccess: () => { refetch() } })}
          />
        )}
      />
      <TicketFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}

export function CompanyUsersPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [featuresUser, setFeaturesUser] = useState<Record<string, unknown> | null>(null)
  const [editUser, setEditUser] = useState<AdminUser | null>(null)
  const [resetUser, setResetUser] = useState<AdminUser | null>(null)
  const deleteUser = useDeleteEntity('/users', ['company-users'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('company-users', '/users')
  const toggleStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const action = status === 'active' ? 'suspend' : 'activate'
      await api.post(`/users/${id}/${action}`)
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['company-users'] })
      refetch()
    },
  })
  const rows = Array.isArray(items) ? items : []
  const onSaved = () => {
    qc.invalidateQueries({ queryKey: ['company-users'] })
    refetch()
  }
  return (
    <div>
      <DataTable
        title={t('users')}
        subtitle={t('company_users_help')}
        loading={isLoading}
        exportFilename="users"
        data={rows}
        columns={[
          { key: 'username', label: t('username') },
          { key: 'full_name_ar', label: t('name_ar') },
          { key: 'email', label: t('email') },
          { key: 'system_role', label: t('role'), render: (row) => roleLabel(String(row.system_role ?? '')) },
          { key: 'status', label: t('status') },
        ]}
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus className="me-2 h-4 w-4" />
            {t('add_user')}
          </Button>
        }
        rowActions={(row) => (
          <RowActions
            onEdit={() => setEditUser(row as unknown as AdminUser)}
            onDelete={() => confirmDelete(t) && deleteUser.mutate(row.id as number, { onSuccess: () => { refetch() } })}
            extra={
              <>
                <Button
                  variant="secondary"
                  className="!px-2 !py-1.5 text-xs"
                  onClick={() => setFeaturesUser(row)}
                  title={t('user_feature_access')}
                >
                  <Sliders className="me-1 h-3.5 w-3.5 text-primary-600" />
                  {t('features')}
                </Button>
                <Button
                  variant="secondary"
                  className="!px-2 !py-1.5 text-xs"
                  onClick={() => setResetUser(row as unknown as AdminUser)}
                  title={t('reset_password')}
                >
                  <KeyRound className="me-1 h-3.5 w-3.5 text-amber-600" />
                  {t('reset_password')}
                </Button>
                <Button
                  variant="secondary"
                  className="!px-2 !py-1.5 text-xs"
                  loading={toggleStatus.isPending && toggleStatus.variables?.id === row.id}
                  onClick={() => toggleStatus.mutate({ id: row.id as number, status: String(row.status) })}
                  title={row.status === 'active' ? t('suspend') : t('activate')}
                >
                  <Power className="me-1 h-3.5 w-3.5" />
                  {row.status === 'active' ? t('suspend') : t('activate')}
                </Button>
              </>
            }
          />
        )}
      />
      <UserFormModal open={open} onClose={() => { setOpen(false); refetch() }} />
      <UserEditModal
        open={!!editUser}
        user={editUser}
        showCompanyId={false}
        onClose={() => setEditUser(null)}
        onSaved={onSaved}
      />
      <ResetPasswordModal
        open={!!resetUser}
        userId={resetUser?.id ?? null}
        userEmail={resetUser?.email ?? ''}
        onClose={() => setResetUser(null)}
      />
      <UserFeaturesModal
        open={!!featuresUser}
        userId={featuresUser?.id as number}
        userName={String((i18n.language === 'ar' ? featuresUser?.full_name_ar : featuresUser?.full_name_en) ?? '')}
        onClose={() => setFeaturesUser(null)}
        onSaved={onSaved}
      />
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
