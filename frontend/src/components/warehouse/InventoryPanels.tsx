import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { ArrowLeftRight, Plus, Truck } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { useModuleList } from '@/hooks/useModuleList'
import { useWarehousesLookup, useProjectsLookup } from '@/hooks/useLookupData'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import api from '@/lib/api'

function SelectField({ label, value, onChange, options, required }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  required?: boolean
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      <select className="input-field" value={value} onChange={(e) => onChange(e.target.value)} required={required}>
        <option value="">—</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

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

export function EquipmentPanel() {
  const { t, i18n } = useTranslation()
  const modal = useCrudModal()
  const deleteEq = useDeleteEntity('/warehouse/equipment', ['warehouse-equipment'])
  const { data, isLoading, refetch } = useModuleList<Record<string, unknown>[]>('warehouse-equipment', '/warehouse/equipment')
  const rows = Array.isArray(data) ? data : []

  const name = (row: Record<string, unknown>) =>
    i18n.language === 'ar' ? String(row.name_ar) : String(row.name_en)

  return (
    <>
      <DataTable
        title={t('heavy_equipment')}
        subtitle={t('heavy_equipment_help')}
        loading={isLoading}
        exportFilename="equipment"
        data={rows}
        actions={
          <Button onClick={modal.openCreate}>
            <Plus className="me-2 h-4 w-4" />{t('add_equipment')}
          </Button>
        }
        emptyActionLabel={t('add_equipment')}
        onEmptyAction={modal.openCreate}
        columns={[
          { key: 'asset_code', label: t('asset_code') },
          { key: 'name', label: t('name'), render: (row) => name(row) },
          { key: 'equipment_type', label: t('equipment_type') },
          { key: 'status', label: t('status') },
          { key: 'warehouse_name', label: t('current_location') },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deleteEq.mutate(row.id as number, { onSuccess: () => refetch() })}
          />
        )}
      />
      <EquipmentFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </>
  )
}

export function StockTransfersPanel() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [eqOpen, setEqOpen] = useState(false)
  const { data: movements, isLoading: movLoading, refetch: refetchMov } = useModuleList<Record<string, unknown>[]>('warehouse-movements', '/warehouse/movements')
  const { data: eqTransfers, isLoading: eqLoading, refetch: refetchEq } = useModuleList<Record<string, unknown>[]>('equipment-transfers', '/warehouse/equipment/transfers')
  const movRows = Array.isArray(movements) ? movements : []
  const eqRows = Array.isArray(eqTransfers) ? eqTransfers : []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => setOpen(true)}>
          <ArrowLeftRight className="me-2 h-4 w-4" />{t('transfer_materials')}
        </Button>
        <Button variant="secondary" onClick={() => setEqOpen(true)}>
          <Truck className="me-2 h-4 w-4" />{t('transfer_equipment')}
        </Button>
      </div>

      <DataTable
        title={t('material_transfers')}
        subtitle={t('material_transfers_help')}
        loading={movLoading}
        exportFilename="stock-movements"
        data={movRows}
        columns={[
          { key: 'item_sku', label: 'SKU' },
          { key: 'item_name', label: t('name') },
          { key: 'quantity', label: t('quantity') },
          { key: 'from_warehouse_name', label: t('from_warehouse') },
          { key: 'to_warehouse_name', label: t('to_warehouse') },
          { key: 'reference', label: t('reference') },
          { key: 'created_at', label: t('date'), render: (row) => String(row.created_at ?? '').slice(0, 10) },
        ]}
      />

      <DataTable
        title={t('equipment_transfers')}
        subtitle={t('equipment_transfers_help')}
        loading={eqLoading}
        exportFilename="equipment-transfers"
        data={eqRows}
        columns={[
          { key: 'asset_code', label: t('asset_code') },
          { key: 'equipment_name', label: t('name') },
          { key: 'from_warehouse_name', label: t('from_warehouse') },
          { key: 'to_warehouse_name', label: t('to_warehouse') },
          { key: 'reference', label: t('reference') },
          { key: 'created_at', label: t('date'), render: (row) => String(row.created_at ?? '').slice(0, 10) },
        ]}
      />

      <StockTransferModal
        open={open}
        onClose={() => { setOpen(false); refetchMov() }}
      />
      <EquipmentTransferModal
        open={eqOpen}
        onClose={() => { setEqOpen(false); refetchEq() }}
      />
    </div>
  )
}

function EquipmentFormModal({
  open,
  onClose,
  editRow,
}: {
  open: boolean
  onClose: () => void
  editRow: Record<string, unknown> | null
}) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: warehouses = [] } = useWarehousesLookup()
  const { data: projects = [] } = useProjectsLookup()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    asset_code: '',
    name_ar: '',
    name_en: '',
    equipment_type: 'excavator',
    serial_number: '',
    status: 'available',
    current_warehouse_id: '',
    project_id: '',
    notes: '',
  })

  const reset = () => {
    if (editRow) {
      setForm({
        asset_code: String(editRow.asset_code ?? ''),
        name_ar: String(editRow.name_ar ?? ''),
        name_en: String(editRow.name_en ?? ''),
        equipment_type: String(editRow.equipment_type ?? 'excavator'),
        serial_number: String(editRow.serial_number ?? ''),
        status: String(editRow.status ?? 'available'),
        current_warehouse_id: String(editRow.current_warehouse_id ?? ''),
        project_id: String(editRow.project_id ?? ''),
        notes: String(editRow.notes ?? ''),
      })
    } else {
      setForm({
        asset_code: '',
        name_ar: '',
        name_en: '',
        equipment_type: 'excavator',
        serial_number: '',
        status: 'available',
        current_warehouse_id: warehouses.length ? String(warehouses[0].id) : '',
        project_id: '',
        notes: '',
      })
    }
  }

  useEffect(() => {
    if (open) reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editRow, open, warehouses])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        asset_code: form.asset_code,
        name_ar: form.name_ar,
        name_en: form.name_en,
        equipment_type: form.equipment_type,
        serial_number: form.serial_number || null,
        status: form.status,
        current_warehouse_id: form.current_warehouse_id ? Number(form.current_warehouse_id) : null,
        project_id: form.project_id ? Number(form.project_id) : null,
        notes: form.notes || null,
      }
      if (editRow?.id) {
        const { asset_code: _, ...update } = payload
        await api.put(`/warehouse/equipment/${editRow.id}`, update)
      } else {
        await api.post('/warehouse/equipment', payload)
      }
      qc.invalidateQueries({ queryKey: ['warehouse-equipment'] })
      qc.invalidateQueries({ queryKey: ['warehouse-summary'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_equipment') : t('add_equipment')}>
      <form onSubmit={submit} className="space-y-4">
        {!editRow && (
          <Input label={t('asset_code')} value={form.asset_code} onChange={(e) => setForm({ ...form, asset_code: e.target.value })} required />
        )}
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <SelectField
          label={t('equipment_type')}
          value={form.equipment_type}
          onChange={(v) => setForm({ ...form, equipment_type: v })}
          options={[
            { value: 'excavator', label: t('excavator') },
            { value: 'crane', label: t('crane') },
            { value: 'mixer', label: t('mixer') },
            { value: 'loader', label: t('loader') },
            { value: 'other', label: t('other') },
          ]}
        />
        <Input label={t('serial_number')} value={form.serial_number} onChange={(e) => setForm({ ...form, serial_number: e.target.value })} />
        <SelectField
          label={t('warehouse')}
          value={form.current_warehouse_id}
          onChange={(v) => setForm({ ...form, current_warehouse_id: v })}
          options={warehouses.map((w) => ({ value: String(w.id), label: String(w.name_en) }))}
        />
        <SelectField
          label={t('project')}
          value={form.project_id}
          onChange={(v) => setForm({ ...form, project_id: v })}
          options={[{ value: '', label: '—' }, ...projects.map((p) => ({ value: String(p.id), label: String(p.name_en) }))]}
        />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

function StockTransferModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: warehouses = [] } = useWarehousesLookup()
  const { data: items = [] } = useModuleList<Record<string, unknown>[]>('warehouse-items', '/warehouse/items')
  const invItems = Array.isArray(items) ? items : []
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    item_id: '',
    from_warehouse_id: '',
    to_warehouse_id: '',
    quantity: '',
    reference: '',
    notes: '',
  })

  const filteredItems = form.from_warehouse_id
    ? invItems.filter((i) => String(i.warehouse_id) === form.from_warehouse_id)
    : invItems

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/warehouse/transfers', {
        item_id: Number(form.item_id),
        from_warehouse_id: Number(form.from_warehouse_id),
        to_warehouse_id: Number(form.to_warehouse_id),
        quantity: form.quantity,
        reference: form.reference || null,
        notes: form.notes || null,
      })
      qc.invalidateQueries({ queryKey: ['warehouse-items'] })
      qc.invalidateQueries({ queryKey: ['warehouse-movements'] })
      qc.invalidateQueries({ queryKey: ['warehouse-summary'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('transfer_materials')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField
          label={t('from_warehouse')}
          value={form.from_warehouse_id}
          onChange={(v) => setForm({ ...form, from_warehouse_id: v, item_id: '' })}
          required
          options={warehouses.map((w) => ({ value: String(w.id), label: `${w.code} — ${w.name_en}` }))}
        />
        <SelectField
          label={t('raw_material')}
          value={form.item_id}
          onChange={(v) => setForm({ ...form, item_id: v })}
          required
          options={filteredItems.map((i) => ({
            value: String(i.id),
            label: `${i.sku} — ${i.name_en} (${i.quantity} ${i.unit})`,
          }))}
        />
        <SelectField
          label={t('to_warehouse')}
          value={form.to_warehouse_id}
          onChange={(v) => setForm({ ...form, to_warehouse_id: v })}
          required
          options={warehouses.map((w) => ({ value: String(w.id), label: `${w.code} — ${w.name_en}` }))}
        />
        <Input label={t('quantity')} value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} required />
        <Input label={t('reference')} value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('transfer')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

function EquipmentTransferModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: warehouses = [] } = useWarehousesLookup()
  const { data: projects = [] } = useProjectsLookup()
  const { data: equipment = [] } = useModuleList<Record<string, unknown>[]>('warehouse-equipment', '/warehouse/equipment')
  const eqList = Array.isArray(equipment) ? equipment : []
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    equipment_id: '',
    to_warehouse_id: '',
    to_project_id: '',
    reference: '',
    notes: '',
  })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/warehouse/equipment/transfers', {
        equipment_id: Number(form.equipment_id),
        to_warehouse_id: Number(form.to_warehouse_id),
        to_project_id: form.to_project_id ? Number(form.to_project_id) : null,
        reference: form.reference || null,
        notes: form.notes || null,
      })
      qc.invalidateQueries({ queryKey: ['warehouse-equipment'] })
      qc.invalidateQueries({ queryKey: ['equipment-transfers'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('transfer_equipment')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField
          label={t('heavy_equipment')}
          value={form.equipment_id}
          onChange={(v) => setForm({ ...form, equipment_id: v })}
          required
          options={eqList.map((e) => ({ value: String(e.id), label: `${e.asset_code} — ${e.name_en}` }))}
        />
        <SelectField
          label={t('to_warehouse')}
          value={form.to_warehouse_id}
          onChange={(v) => setForm({ ...form, to_warehouse_id: v })}
          required
          options={warehouses.map((w) => ({ value: String(w.id), label: `${w.code} — ${w.name_en}` }))}
        />
        <SelectField
          label={t('project')}
          value={form.to_project_id}
          onChange={(v) => setForm({ ...form, to_project_id: v })}
          options={[{ value: '', label: '—' }, ...projects.map((p) => ({ value: String(p.id), label: String(p.name_en) }))]}
        />
        <Input label={t('reference')} value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('transfer')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
