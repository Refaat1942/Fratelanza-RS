import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ShoppingCart, Plus } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { ReportLinkButton } from '@/components/ui/ReportLinkButton'
import { useListData } from '@/hooks/useListData'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { Button } from '@/components/ui/Button'
import { VendorFormModal } from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { cn } from '@/lib/utils'

type Tab = 'vendors' | 'rfqs' | 'orders'

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

export function ProcurementPage() {
  const { t, i18n } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const [tab, setTab] = useState<Tab>('vendors')
  const modal = useCrudModal()
  const deleteVendor = useDeleteEntity('/procurement/vendors', ['vendors'])
  const { items: vendors, isLoading: vendorsLoading, refetch } = useListData<Record<string, unknown>>('vendors', '/procurement/vendors')
  const { items: rfqs, isLoading: rfqsLoading } = useListData<Record<string, unknown>>('rfqs', '/procurement/rfqs')
  const { items: orders, isLoading: ordersLoading } = useListData<Record<string, unknown>>('purchase-orders', '/procurement/purchase-orders')

  const tabs: { key: Tab; label: string }[] = [
    { key: 'vendors', label: t('vendors') },
    { key: 'rfqs', label: t('rfqs') },
    { key: 'orders', label: t('purchase_orders') },
  ]

  const reportKey = tab === 'orders' ? 'procurement_orders' : 'procurement_vendors'

  return (
    <div>
      <PageHeader
        title={t('procurement')}
        subtitle={t('procurement_help')}
        icon={ShoppingCart}
        accentIndex={6}
        actions={
          <>
            <ReportLinkButton reportKey={reportKey} />
            {tab === 'vendors' && (
              <Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_vendor')}</Button>
            )}
          </>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={cn(
              'rounded-lg px-3 py-1.5 text-sm font-medium',
              tab === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'vendors' && (
        <DataTable
          title={t('vendors')}
          loading={vendorsLoading}
          exportFilename="vendors"
          data={vendors}
          columns={[
            { key: 'name_ar', label: t('name_ar'), render: (row) => String(i18n.language === 'ar' ? row.name_ar : row.name_en) },
            { key: 'contact_person', label: t('contact_person') },
            { key: 'phone', label: t('mobile') },
            { key: 'rating', label: t('rating') },
          ]}
          rowActions={(row) => (
            <RowActions
              onEdit={() => modal.openEdit(row)}
              onDelete={() => confirmDelete(t) && deleteVendor.mutate(row.id as number, { onSuccess: () => refetch() })}
            />
          )}
        />
      )}

      {tab === 'rfqs' && (
        <DataTable
          title={t('rfqs')}
          loading={rfqsLoading}
          exportFilename="rfqs"
          data={rfqs}
          columns={[
            { key: 'rfq_number', label: '#' },
            { key: 'title', label: t('title') },
            { key: 'status', label: t('status') },
          ]}
        />
      )}

      {tab === 'orders' && (
        <DataTable
          title={t('purchase_orders')}
          loading={ordersLoading}
          exportFilename="purchase-orders"
          data={orders}
          columns={[
            { key: 'po_number', label: '#' },
            { key: 'vendor_id', label: t('vendors') },
            { key: 'total_amount', label: t('amount'), render: (row) => formatEGP(row.total_amount as number) },
            { key: 'status', label: t('status') },
          ]}
        />
      )}

      <VendorFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}
