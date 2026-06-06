import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Package, Warehouse as WarehouseIcon, AlertTriangle, Boxes, Plus, LayoutGrid } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { StatCard } from '@/components/ui/StatCard'
import { Button } from '@/components/ui/Button'
import { useListData } from '@/hooks/useListData'
import { useModuleList } from '@/hooks/useModuleList'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { WarehouseFormModal, WarehouseItemFormModal } from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'inventory' | 'warehouses' | 'overview'

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

export function WarehousePage() {
  const { t, i18n } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const [tab, setTab] = useState<Tab>('inventory')
  const modal = useCrudModal()
  const [itemOpen, setItemOpen] = useState(false)
  const [editItem, setEditItem] = useState<Record<string, unknown> | null>(null)
  const deleteWh = useDeleteEntity('/warehouse', ['warehouse'])
  const deleteItem = useDeleteEntity('/warehouse/items', ['warehouse-items'])
  const { items: warehouses, isLoading: whLoading, refetch: refetchWh } = useListData<Record<string, unknown>>('warehouse', '/warehouse')
  const { data: inventoryData, isLoading: itemsLoading, refetch: refetchItems } = useModuleList<Record<string, unknown>[]>('warehouse-items', '/warehouse/items')
  const invItems = Array.isArray(inventoryData) ? inventoryData : []

  const { data: summary } = useQuery({
    queryKey: ['warehouse-summary'],
    queryFn: async () => (await api.get('/warehouse/summary')).data,
  })

  const tabs: { key: Tab; label: string; icon: typeof Package }[] = [
    { key: 'inventory', label: t('inventory'), icon: Package },
    { key: 'warehouses', label: t('warehouse_locations'), icon: WarehouseIcon },
    { key: 'overview', label: t('overview'), icon: LayoutGrid },
  ]

  const itemName = (row: Record<string, unknown>) =>
    i18n.language === 'ar' ? String(row.name_ar) : String(row.name_en)

  return (
    <div>
      <PageHeader
        title={t('warehouse')}
        subtitle={t('warehouse_about')}
        icon={WarehouseIcon}
        accentIndex={5}
        actions={
          <>
            <Button variant="secondary" onClick={() => modal.openCreate()}>
              <Plus className="me-2 h-4 w-4" />{t('add_warehouse')}
            </Button>
            <Button onClick={() => { setEditItem(null); setItemOpen(true) }}>
              <Plus className="me-2 h-4 w-4" />{t('add_item')}
            </Button>
          </>
        }
      />

      <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <p className="font-medium text-slate-900">{t('warehouse_explainer_title')}</p>
        <p className="mt-1">{t('warehouse_explainer_body')}</p>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title={t('inventory_items')} value={formatInteger(summary?.items_count)} icon={Boxes} />
        <StatCard title={t('warehouse_locations')} value={formatInteger(summary?.warehouses_count)} icon={WarehouseIcon} color="bg-blue-50 text-blue-700" />
        <StatCard title={t('low_stock_items')} value={formatInteger(summary?.low_stock_count)} icon={AlertTriangle} color="bg-red-50 text-red-700" />
        <StatCard title={t('total_stock_qty')} value={formatInteger(summary?.total_quantity)} icon={Package} color="bg-emerald-50 text-emerald-700" />
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium',
              tab === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
            )}
          >
            <Icon className="h-4 w-4" />{label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <DataTable
            title={t('inventory')}
            subtitle={t('inventory_overview_help')}
            loading={itemsLoading}
            exportFilename="inventory"
            data={invItems.slice(0, 8)}
            columns={[
              { key: 'sku', label: 'SKU' },
              { key: 'name', label: t('name'), render: (row) => itemName(row) },
              { key: 'warehouse_code', label: t('warehouse') },
              { key: 'quantity', label: t('quantity'), render: (row) => `${row.quantity} ${row.unit}` },
              { key: 'low_stock', label: t('stock_alert'), render: (row) => row.low_stock ? '⚠️' : '✓' },
            ]}
          />
          <DataTable
            title={t('warehouse_locations')}
            loading={whLoading}
            exportFilename="warehouses"
            data={warehouses}
            columns={[
              { key: 'code', label: 'Code' },
              { key: 'name_en', label: t('name') },
              { key: 'location', label: t('location') },
            ]}
          />
        </div>
      )}

      {tab === 'inventory' && (
        <DataTable
          title={t('inventory')}
          subtitle={t('inventory_help')}
          loading={itemsLoading}
          exportFilename="inventory"
          data={invItems}
          emptyActionLabel={t('add_item')}
          onEmptyAction={() => { setEditItem(null); setItemOpen(true) }}
          columns={[
            { key: 'sku', label: 'SKU' },
            { key: 'name', label: t('name'), render: (row) => itemName(row) },
            { key: 'warehouse_code', label: t('warehouse') },
            { key: 'quantity', label: t('quantity'), render: (row) => `${row.quantity} ${row.unit}` },
            { key: 'min_stock_level', label: t('min_stock') },
            { key: 'low_stock', label: t('stock_alert'), render: (row) => (
              row.low_stock
                ? <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">{t('low_stock')}</span>
                : <span className="text-emerald-600">{t('ok')}</span>
            ) },
          ]}
          rowActions={(row) => (
            <RowActions
              onEdit={() => { setEditItem(row); setItemOpen(true) }}
              onDelete={() => confirmDelete(t) && deleteItem.mutate(row.id as number, { onSuccess: () => { refetchItems() } })}
            />
          )}
        />
      )}

      {tab === 'warehouses' && (
        <DataTable
          title={t('warehouse_locations')}
          subtitle={t('warehouse_locations_help')}
          loading={whLoading}
          exportFilename="warehouse"
          data={warehouses}
          actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_warehouse')}</Button>}
          emptyActionLabel={t('add_warehouse')}
          onEmptyAction={modal.openCreate}
          columns={[
            { key: 'code', label: 'Code' },
            { key: 'name_ar', label: t('name_ar') },
            { key: 'name_en', label: t('name_en') },
            { key: 'location', label: t('location') },
          ]}
          rowActions={(row) => (
            <RowActions
              onEdit={() => modal.openEdit(row)}
              onDelete={() => confirmDelete(t) && deleteWh.mutate(row.id as number, { onSuccess: () => { refetchWh() } })}
            />
          )}
        />
      )}

      <WarehouseFormModal open={modal.open} onClose={() => { modal.close(); refetchWh() }} editRow={modal.editRow} />
      <WarehouseItemFormModal
        open={itemOpen}
        onClose={() => { setItemOpen(false); setEditItem(null); refetchItems() }}
        editRow={editItem}
      />
    </div>
  )
}
