import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { LayoutGrid, List, Plus } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { useModuleList } from '@/hooks/useModuleList'
import { Button } from '@/components/ui/Button'
import { UnitsBoard } from '@/components/real-estate/UnitsBoard'
import { UserFormModal } from '@/components/forms/UserFormModal'
import { cn } from '@/lib/utils'
import api from '@/lib/api'

function useListData<T>(key: string, endpoint: string) {
  const { data, isLoading, refetch } = useModuleList<T[] | { items: T[] }>(key, endpoint)
  const items = Array.isArray(data) ? data : (data as { items?: T[] })?.items ?? []
  return { items, isLoading, refetch }
}

export function ProjectsPage() {
  const { t } = useTranslation()
  const [view, setView] = useState<'list' | 'board'>('board')
  const { items, isLoading } = useListData<Record<string, unknown>>('projects', '/projects')
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t('projects')}</h1>
        <div className="flex rounded-lg border border-slate-200 bg-white p-1">
          <button
            onClick={() => setView('board')}
            className={cn('flex items-center gap-1 rounded px-3 py-1.5 text-sm', view === 'board' && 'bg-primary-100 text-primary-700')}
          >
            <LayoutGrid className="h-4 w-4" /> {t('units_board')}
          </button>
          <button
            onClick={() => setView('list')}
            className={cn('flex items-center gap-1 rounded px-3 py-1.5 text-sm', view === 'list' && 'bg-primary-100 text-primary-700')}
          >
            <List className="h-4 w-4" /> {t('projects_list')}
          </button>
        </div>
      </div>
      {view === 'board' ? (
        <UnitsBoard />
      ) : (
        <DataTable
          title={t('projects')}
          loading={isLoading}
          data={items}
          columns={[
            { key: 'id', label: '#' },
            { key: 'name_ar', label: t('projects') },
            { key: 'code', label: 'Code' },
            { key: 'status', label: t('status') },
            { key: 'total_units', label: t('units') },
          ]}
        />
      )}
    </div>
  )
}

export function ReservationsPage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('reservations', '/reservations')
  return (
    <DataTable
      title={t('reservations')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'reservation_number', label: '#' },
        { key: 'customer_id', label: t('customers') },
        { key: 'unit_id', label: t('units') },
        { key: 'status', label: t('status') },
        { key: 'expiry_date', label: 'Expiry' },
      ]}
    />
  )
}

export function ContractsPage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('contracts', '/contracts')
  return (
    <DataTable
      title={t('contracts')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'contract_number', label: '#' },
        { key: 'customer_id', label: t('customers') },
        { key: 'total_price', label: t('total_sales') },
        { key: 'status', label: t('status') },
        { key: 'contract_date', label: 'Date' },
      ]}
    />
  )
}

export function CollectionsPage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('installments', '/collections/installments')
  return (
    <DataTable
      title={t('collections')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'contract_number', label: t('contracts') },
        { key: 'installment_number', label: '#' },
        { key: 'due_date', label: 'Due' },
        { key: 'due_amount', label: 'Amount' },
        { key: 'status', label: t('status') },
      ]}
    />
  )
}

export function BrokersPage() {
  const { t, i18n } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('brokers', '/brokers')
  return (
    <DataTable
      title={t('brokers')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'id', label: '#' },
        {
          key: 'name',
          label: t('brokers'),
          render: (row) => String(i18n.language === 'ar' ? row.name_ar : row.name_en),
        },
        { key: 'mobile', label: 'Mobile' },
        { key: 'commission_rate', label: 'Rate %' },
        { key: 'rank_score', label: 'Rank' },
      ]}
    />
  )
}

export function FinancePage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('accounts', '/finance/accounts')
  return (
    <DataTable
      title={t('finance')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'code', label: 'Code' },
        { key: 'name_ar', label: t('finance') },
        { key: 'account_type', label: 'Type' },
      ]}
    />
  )
}

export function ConstructionPage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('phases', '/construction/phases')
  return (
    <DataTable
      title={t('construction')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'name_ar', label: t('construction') },
        { key: 'progress_percent', label: 'Progress %' },
        { key: 'planned_cost', label: 'Planned' },
        { key: 'actual_cost', label: 'Actual' },
      ]}
    />
  )
}

export function ProcurementPage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('vendors', '/procurement/vendors')
  return (
    <DataTable
      title={t('procurement')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'name_ar', label: 'Vendor' },
        { key: 'rating', label: 'Rating' },
      ]}
    />
  )
}

export function WarehousePage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('warehouse', '/warehouse')
  return (
    <DataTable
      title={t('warehouse')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'code', label: 'Code' },
        { key: 'name_ar', label: t('warehouse') },
        { key: 'location', label: 'Location' },
      ]}
    />
  )
}

export function PropertyPage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('maintenance', '/property/maintenance')
  return (
    <DataTable
      title={t('property')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'title', label: 'Request' },
        { key: 'unit_id', label: t('units') },
        { key: 'priority', label: 'Priority' },
        { key: 'status', label: t('status') },
      ]}
    />
  )
}

export function CustomerServicePage() {
  const { t } = useTranslation()
  const { items, isLoading } = useListData<Record<string, unknown>>('tickets', '/tickets')
  return (
    <DataTable
      title={t('customer_service')}
      loading={isLoading}
      data={items}
      columns={[
        { key: 'ticket_number', label: '#' },
        { key: 'subject', label: 'Subject' },
        { key: 'category', label: 'Category' },
        { key: 'priority', label: 'Priority' },
        { key: 'status', label: t('status') },
      ]}
    />
  )
}

export function CompanyUsersPage() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('company-users', '/users')
  const rows = Array.isArray(items) ? items : []
  return (
    <div>
      <DataTable
        title={t('users')}
        loading={isLoading}
        data={rows}
        columns={[
          { key: 'email', label: t('email') },
          { key: 'full_name_ar', label: t('name_ar') },
          { key: 'system_role', label: t('role') },
          { key: 'status', label: t('status') },
        ]}
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus className="me-2 h-4 w-4" />
            {t('add_user')}
          </Button>
        }
      />
      <UserFormModal open={open} onClose={() => { setOpen(false); refetch() }} />
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
