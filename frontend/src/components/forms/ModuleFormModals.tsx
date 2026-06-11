import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useCustomersLookup, useFloorsLookup, useProjectsLookup, useUnitsLookup, useWarehousesLookup } from '@/hooks/useLookupData'
import api from '@/lib/api'

interface ModalProps {
  open: boolean
  onClose: () => void
  editRow?: Record<string, unknown> | null
}

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

export function ProjectFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name_ar: '', name_en: '', code: '', city: '', status: 'active' })

  useEffect(() => {
    if (editRow) {
      setForm({
        name_ar: String(editRow.name_ar ?? ''),
        name_en: String(editRow.name_en ?? ''),
        code: String(editRow.code ?? ''),
        city: String(editRow.city ?? ''),
        status: String(editRow.status ?? 'active'),
      })
    } else {
      setForm({ name_ar: '', name_en: '', code: '', city: '', status: 'active' })
    }
  }, [editRow, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (editRow?.id) {
        await api.put(`/projects/${editRow.id}`, form)
      } else {
        await api.post('/projects', form)
      }
      qc.invalidateQueries({ queryKey: ['projects'] })
      qc.invalidateQueries({ queryKey: ['projects-lookup'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_project') : t('add_project')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <Input label="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
        <Input label={t('city')} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
        <SelectField label={t('status')} value={form.status} onChange={(v) => setForm({ ...form, status: v })} options={[
          { value: 'planning', label: 'Planning' },
          { value: 'active', label: 'Active' },
          { value: 'completed', label: 'Completed' },
        ]} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function UnitFormModal({ open, onClose }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: floors = [] } = useFloorsLookup()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    floor_id: '', unit_code: '', unit_number: '', unit_type: 'apartment', area_sqm: '120', bedrooms: '2', bathrooms: '2', price: '2500000',
  })

  useEffect(() => {
    if (open && floors.length && !form.floor_id) {
      setForm((f) => ({ ...f, floor_id: String(floors[0].id) }))
    }
  }, [open, floors, form.floor_id])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/projects/units', {
        floor_id: Number(form.floor_id),
        unit_code: form.unit_code,
        unit_number: form.unit_number,
        unit_type: form.unit_type,
        area_sqm: form.area_sqm,
        bedrooms: Number(form.bedrooms),
        bathrooms: Number(form.bathrooms),
        price: form.price,
      })
      qc.invalidateQueries({ queryKey: ['units-board'] })
      qc.invalidateQueries({ queryKey: ['units-lookup'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('add_unit')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('floor')} value={form.floor_id} onChange={(v) => setForm({ ...form, floor_id: v })} required
          options={floors.map((f) => ({ value: String(f.id), label: `${f.project_name} - ${f.name_ar}` }))} />
        <Input label="Unit Code" value={form.unit_code} onChange={(e) => setForm({ ...form, unit_code: e.target.value })} required />
        <Input label="Unit #" value={form.unit_number} onChange={(e) => setForm({ ...form, unit_number: e.target.value })} required />
        <SelectField label="Type" value={form.unit_type} onChange={(v) => setForm({ ...form, unit_type: v })} options={[
          { value: 'apartment', label: 'Apartment' },
          { value: 'villa', label: 'Villa' },
          { value: 'shop', label: 'Shop' },
        ]} />
        <Input label="Area (m²)" value={form.area_sqm} onChange={(e) => setForm({ ...form, area_sqm: e.target.value })} required />
        <Input label={t('price')} value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function ReservationFormModal({ open, onClose, editRow, preselectedUnitId }: ModalProps & { preselectedUnitId?: number }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: customers = [] } = useCustomersLookup()
  const { data: units = [] } = useUnitsLookup(true)
  const today = new Date().toISOString().slice(0, 10)
  const expiry = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    customer_id: '', unit_id: preselectedUnitId ? String(preselectedUnitId) : '',
    deposit_amount: '100000', reservation_date: today, expiry_date: expiry, notes: '',
  })

  useEffect(() => {
    if (preselectedUnitId) setForm((f) => ({ ...f, unit_id: String(preselectedUnitId) }))
    if (editRow) {
      setForm({
        customer_id: String(editRow.customer_id ?? ''),
        unit_id: String(editRow.unit_id ?? ''),
        deposit_amount: String(editRow.deposit_amount ?? '0'),
        reservation_date: String(editRow.reservation_date ?? today),
        expiry_date: String(editRow.expiry_date ?? expiry),
        notes: String(editRow.notes ?? ''),
      })
    }
  }, [editRow, preselectedUnitId, open, today, expiry])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        customer_id: Number(form.customer_id),
        unit_id: Number(form.unit_id),
        deposit_amount: form.deposit_amount,
        reservation_date: form.reservation_date,
        expiry_date: form.expiry_date,
        notes: form.notes || undefined,
      }
      if (editRow?.id) {
        await api.put(`/reservations/${editRow.id}`, payload)
      } else {
        await api.post('/reservations', payload)
      }
      qc.invalidateQueries({ queryKey: ['reservations'] })
      qc.invalidateQueries({ queryKey: ['units-board'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_reservation') : t('add_reservation')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('customers')} value={form.customer_id} onChange={(v) => setForm({ ...form, customer_id: v })} required
          options={customers.map((c) => ({ value: String(c.id), label: c.full_name_ar }))} />
        <SelectField label={t('units')} value={form.unit_id} onChange={(v) => setForm({ ...form, unit_id: v })} required
          options={units.map((u) => ({ value: String(u.id), label: `${u.unit_code} — ${u.price}` }))} />
        <Input label={t('deposit')} value={form.deposit_amount} onChange={(e) => setForm({ ...form, deposit_amount: e.target.value })} />
        <Input label={t('reservation_date')} type="date" value={form.reservation_date} onChange={(e) => setForm({ ...form, reservation_date: e.target.value })} required />
        <Input label={t('expiry_date')} type="date" value={form.expiry_date} onChange={(e) => setForm({ ...form, expiry_date: e.target.value })} required />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function ContractFormModal({ open, onClose, editRow, preselectedReservationId }: ModalProps & { preselectedReservationId?: number }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: customers = [] } = useCustomersLookup()
  const { data: units = [] } = useUnitsLookup()
  const today = new Date().toISOString().slice(0, 10)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    customer_id: '', unit_id: '', reservation_id: preselectedReservationId ? String(preselectedReservationId) : '',
    total_price: '2500000', contract_date: today,
  })

  useEffect(() => {
    if (editRow) {
      setForm({
        customer_id: String(editRow.customer_id ?? ''),
        unit_id: String(editRow.unit_id ?? ''),
        reservation_id: String(editRow.reservation_id ?? ''),
        total_price: String(editRow.total_price ?? ''),
        contract_date: String(editRow.contract_date ?? today),
      })
    }
  }, [editRow, open, today])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        customer_id: Number(form.customer_id),
        unit_id: Number(form.unit_id),
        reservation_id: form.reservation_id ? Number(form.reservation_id) : undefined,
        total_price: form.total_price,
        contract_date: form.contract_date,
      }
      if (editRow?.id) {
        await api.put(`/contracts/${editRow.id}`, payload)
      } else {
        await api.post('/contracts', payload)
      }
      qc.invalidateQueries({ queryKey: ['contracts'] })
      qc.invalidateQueries({ queryKey: ['installments'] })
      qc.invalidateQueries({ queryKey: ['units-board'] })
      qc.invalidateQueries({ queryKey: ['reservations'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_contract') : t('add_contract')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('customers')} value={form.customer_id} onChange={(v) => setForm({ ...form, customer_id: v })} required
          options={customers.map((c) => ({ value: String(c.id), label: c.full_name_ar }))} />
        <SelectField label={t('units')} value={form.unit_id} onChange={(v) => setForm({ ...form, unit_id: v })} required
          options={units.map((u) => ({ value: String(u.id), label: u.unit_code }))} />
        <Input label={t('total_sales')} value={form.total_price} onChange={(e) => setForm({ ...form, total_price: e.target.value })} required />
        <Input label="Date" type="date" value={form.contract_date} onChange={(e) => setForm({ ...form, contract_date: e.target.value })} required />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function PaymentFormModal({ open, onClose, installment }: { open: boolean; onClose: () => void; installment?: Record<string, unknown> | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const today = new Date().toISOString().slice(0, 10)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ amount: '', payment_date: today, payment_method: 'cash', reference_number: '' })

  useEffect(() => {
    if (installment) {
      setForm((f) => ({
        ...f,
        amount: String(installment.remaining_balance ?? installment.due_amount ?? ''),
      }))
    }
  }, [installment, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!installment) return
    setLoading(true)
    try {
      await api.post('/collections/payments', {
        installment_id: installment.id,
        customer_id: installment.customer_id,
        amount: form.amount,
        payment_date: form.payment_date,
        payment_method: form.payment_method,
        reference_number: form.reference_number || undefined,
      })
      qc.invalidateQueries({ queryKey: ['installments'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('record_payment')}>
      <form onSubmit={submit} className="space-y-4">
        <p className="text-sm text-slate-600">
          {String(installment?.contract_number ?? '')} — #{String(installment?.installment_number ?? '')}
        </p>
        <Input label={t('amount')} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
        <Input label="Date" type="date" value={form.payment_date} onChange={(e) => setForm({ ...form, payment_date: e.target.value })} required />
        <SelectField label={t('payment_method')} value={form.payment_method} onChange={(v) => setForm({ ...form, payment_method: v })} options={[
          { value: 'cash', label: 'Cash' },
          { value: 'bank_transfer', label: 'Bank Transfer' },
          { value: 'cheque', label: 'Cheque' },
        ]} />
        <Input label={t('reference')} value={form.reference_number} onChange={(e) => setForm({ ...form, reference_number: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function BrokerFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name_ar: '', name_en: '', mobile: '', email: '', commission_rate: '2.5' })

  useEffect(() => {
    if (editRow) {
      setForm({
        name_ar: String(editRow.name_ar ?? ''),
        name_en: String(editRow.name_en ?? ''),
        mobile: String(editRow.mobile ?? ''),
        email: String(editRow.email ?? ''),
        commission_rate: String(editRow.commission_rate ?? '2.5'),
      })
    } else {
      setForm({ name_ar: '', name_en: '', mobile: '', email: '', commission_rate: '2.5' })
    }
  }, [editRow, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = { ...form, commission_rate: form.commission_rate }
      if (editRow?.id) {
        await api.put(`/brokers/${editRow.id}`, payload)
      } else {
        await api.post('/brokers', payload)
      }
      qc.invalidateQueries({ queryKey: ['brokers'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_broker') : t('add_broker')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <Input label={t('mobile')} value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} required />
        <Input label={t('email')} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <Input label="Commission %" value={form.commission_rate} onChange={(e) => setForm({ ...form, commission_rate: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function WarehouseFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name_ar: '', name_en: '', code: '', location: '' })

  useEffect(() => {
    if (editRow) {
      setForm({
        name_ar: String(editRow.name_ar ?? ''),
        name_en: String(editRow.name_en ?? ''),
        code: String(editRow.code ?? ''),
        location: String(editRow.location ?? ''),
      })
    } else {
      setForm({ name_ar: '', name_en: '', code: '', location: '' })
    }
  }, [editRow, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (editRow?.id) {
        await api.put(`/warehouse/${editRow.id}`, form)
      } else {
        await api.post('/warehouse', form)
      }
      qc.invalidateQueries({ queryKey: ['warehouse'] })
      qc.invalidateQueries({ queryKey: ['warehouses-lookup'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_warehouse') : t('add_warehouse')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <Input label="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
        <Input label="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function WarehouseItemFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: warehouses = [] } = useWarehousesLookup()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ warehouse_id: '', sku: '', name_ar: '', name_en: '', quantity: '0', min_stock_level: '10', unit: 'pcs' })

  useEffect(() => {
    if (editRow) {
      setForm({
        warehouse_id: String(editRow.warehouse_id ?? ''),
        sku: String(editRow.sku ?? ''),
        name_ar: String(editRow.name_ar ?? ''),
        name_en: String(editRow.name_en ?? ''),
        quantity: String(editRow.quantity ?? '0'),
        min_stock_level: String(editRow.min_stock_level ?? '10'),
        unit: String(editRow.unit ?? 'pcs'),
      })
    } else if (open) {
      setForm({ warehouse_id: warehouses.length ? String(warehouses[0].id) : '', sku: '', name_ar: '', name_en: '', quantity: '0', min_stock_level: '10', unit: 'pcs' })
    }
  }, [editRow, open, warehouses])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        warehouse_id: Number(form.warehouse_id),
        sku: form.sku,
        name_ar: form.name_ar,
        name_en: form.name_en,
        quantity: form.quantity,
        min_stock_level: form.min_stock_level,
        unit: form.unit,
      }
      if (editRow?.id) {
        await api.put(`/warehouse/items/${editRow.id}`, {
          name_ar: payload.name_ar,
          name_en: payload.name_en,
          quantity: payload.quantity,
          min_stock_level: payload.min_stock_level,
          unit: payload.unit,
        })
      } else {
        await api.post('/warehouse/items', payload)
      }
      qc.invalidateQueries({ queryKey: ['warehouse-items'] })
      qc.invalidateQueries({ queryKey: ['warehouse-summary'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_item') : t('add_item')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('warehouse')} value={form.warehouse_id} onChange={(v) => setForm({ ...form, warehouse_id: v })} required
          options={warehouses.map((w) => ({ value: String(w.id), label: String(w.name_ar) }))} />
        <Input label="SKU" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} required />
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <Input label={t('quantity')} value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function VendorFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name_ar: '', name_en: '', contact_person: '', phone: '', email: '' })

  useEffect(() => {
    if (editRow) {
      setForm({
        name_ar: String(editRow.name_ar ?? ''),
        name_en: String(editRow.name_en ?? ''),
        contact_person: String(editRow.contact_person ?? ''),
        phone: String(editRow.phone ?? ''),
        email: String(editRow.email ?? ''),
      })
    } else {
      setForm({ name_ar: '', name_en: '', contact_person: '', phone: '', email: '' })
    }
  }, [editRow, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (editRow?.id) {
        await api.put(`/procurement/vendors/${editRow.id}`, form)
      } else {
        await api.post('/procurement/vendors', form)
      }
      qc.invalidateQueries({ queryKey: ['vendors'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_vendor') : t('add_vendor')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <Input label="Contact" value={form.contact_person} onChange={(e) => setForm({ ...form, contact_person: e.target.value })} />
        <Input label={t('mobile')} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <Input label={t('email')} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function ConstructionPhaseFormModal({ open, onClose, editRow, defaultProjectId }: ModalProps & { defaultProjectId?: string }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: projects = [] } = useProjectsLookup()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ project_id: '', name_ar: '', name_en: '', planned_start: '', planned_end: '', progress_percent: '0' })

  useEffect(() => {
    if (editRow) {
      setForm({
        project_id: String(editRow.project_id ?? ''),
        name_ar: String(editRow.name_ar ?? ''),
        name_en: String(editRow.name_en ?? ''),
        planned_start: String(editRow.planned_start ?? ''),
        planned_end: String(editRow.planned_end ?? ''),
        progress_percent: String(editRow.progress_percent ?? '0'),
      })
    } else {
      setForm({
        project_id: defaultProjectId || (projects[0] ? String(projects[0].id) : ''),
        name_ar: '', name_en: '', planned_start: '', planned_end: '', progress_percent: '0',
      })
    }
  }, [editRow, open, projects, defaultProjectId])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        project_id: Number(form.project_id),
        name_ar: form.name_ar,
        name_en: form.name_en,
        planned_start: form.planned_start || undefined,
        planned_end: form.planned_end || undefined,
      }
      const progress = Number(form.progress_percent)
      if (editRow?.id) {
        await api.put(`/construction/phases/${editRow.id}`, { ...payload, progress_percent: progress })
      } else {
        await api.post('/construction/phases', { ...payload, progress_percent: progress })
      }
      qc.invalidateQueries({ queryKey: ['phases'] })
      qc.invalidateQueries({ queryKey: ['construction-schedule'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_phase') : t('add_phase')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('projects')} value={form.project_id} onChange={(v) => setForm({ ...form, project_id: v })} required
          options={projects.map((p) => ({ value: String(p.id), label: String(p.name_ar) }))} />
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <Input label={t('planned_start')} type="date" value={form.planned_start} onChange={(e) => setForm({ ...form, planned_start: e.target.value })} />
        <Input label={t('planned_end')} type="date" value={form.planned_end} onChange={(e) => setForm({ ...form, planned_end: e.target.value })} />
        <Input label={t('progress_percent')} type="number" min={0} max={100} value={form.progress_percent} onChange={(e) => setForm({ ...form, progress_percent: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function ConstructionTaskFormModal({ open, onClose, editRow, projectId }: ModalProps & { projectId?: string }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [phases, setPhases] = useState<Record<string, unknown>[]>([])
  const [siblingTasks, setSiblingTasks] = useState<Record<string, unknown>[]>([])
  const [form, setForm] = useState({
    phase_id: '', name_ar: '', name_en: '', contractor: '', planned_start: '', planned_end: '',
    depends_on_task_id: '', status: 'pending', progress_percent: '0',
  })

  useEffect(() => {
    if (!open) return
    const load = async () => {
      const { data } = await api.get('/construction/phases', { params: projectId ? { project_id: projectId } : {} })
      setPhases(data)
      if (editRow) {
        setForm({
          phase_id: String(editRow.phase_id ?? ''),
          name_ar: String(editRow.name_ar ?? ''),
          name_en: String(editRow.name_en ?? ''),
          contractor: String(editRow.contractor ?? ''),
          planned_start: String(editRow.planned_start ?? ''),
          planned_end: String(editRow.planned_end ?? ''),
          depends_on_task_id: editRow.depends_on_task_id ? String(editRow.depends_on_task_id) : '',
          status: String(editRow.status ?? 'pending'),
          progress_percent: String(editRow.progress_percent ?? '0'),
        })
      } else if (data.length) {
        setForm((f) => ({ ...f, phase_id: String(data[0].id) }))
      }
    }
    load().catch(() => setPhases([]))
  }, [open, editRow, projectId])

  useEffect(() => {
    if (!form.phase_id) { setSiblingTasks([]); return }
    api.get('/construction/tasks', { params: { phase_id: form.phase_id } })
      .then(({ data }) => setSiblingTasks(data.filter((t: Record<string, unknown>) => t.id !== editRow?.id)))
      .catch(() => setSiblingTasks([]))
  }, [form.phase_id, editRow?.id])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        phase_id: Number(form.phase_id),
        name_ar: form.name_ar,
        name_en: form.name_en,
        contractor: form.contractor || undefined,
        planned_start: form.planned_start || undefined,
        planned_end: form.planned_end || undefined,
        depends_on_task_id: form.depends_on_task_id ? Number(form.depends_on_task_id) : undefined,
        status: form.status,
        progress_percent: Number(form.progress_percent),
      }
      if (editRow?.id) {
        await api.put(`/construction/tasks/${editRow.id}`, payload)
      } else {
        await api.post('/construction/tasks', payload)
      }
      qc.invalidateQueries({ queryKey: ['construction-tasks'] })
      qc.invalidateQueries({ queryKey: ['phases'] })
      qc.invalidateQueries({ queryKey: ['construction-schedule'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_task') : t('add_task')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('phase')} value={form.phase_id} onChange={(v) => setForm({ ...form, phase_id: v })} required
          options={phases.map((p) => ({ value: String(p.id), label: String(p.name_ar) }))} />
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
        <Input label={t('contractor')} value={form.contractor} onChange={(e) => setForm({ ...form, contractor: e.target.value })} />
        <Input label={t('planned_start')} type="date" value={form.planned_start} onChange={(e) => setForm({ ...form, planned_start: e.target.value })} />
        <Input label={t('planned_end')} type="date" value={form.planned_end} onChange={(e) => setForm({ ...form, planned_end: e.target.value })} />
        <SelectField label={t('depends_on_task')} value={form.depends_on_task_id} onChange={(v) => setForm({ ...form, depends_on_task_id: v })}
          options={siblingTasks.map((t) => ({ value: String(t.id), label: String(t.name_ar) }))} />
        <SelectField label={t('status')} value={form.status} onChange={(v) => setForm({ ...form, status: v })} options={[
          { value: 'pending', label: t('status_pending') },
          { value: 'in_progress', label: t('status_in_progress') },
          { value: 'completed', label: t('status_completed') },
        ]} />
        <Input label={t('progress_percent')} type="number" min={0} max={100} value={form.progress_percent} onChange={(e) => setForm({ ...form, progress_percent: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function LeadFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: projects = [] } = useProjectsLookup()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    full_name: '', mobile: '', email: '', source: 'website', stage: 'new', project_id: '', notes: '',
  })

  useEffect(() => {
    if (editRow) {
      setForm({
        full_name: String(editRow.full_name ?? ''),
        mobile: String(editRow.mobile ?? ''),
        email: String(editRow.email ?? ''),
        source: String(editRow.source ?? 'website'),
        stage: String(editRow.stage ?? 'new'),
        project_id: editRow.project_id ? String(editRow.project_id) : '',
        notes: String(editRow.notes ?? ''),
      })
    } else {
      setForm({ full_name: '', mobile: '', email: '', source: 'website', stage: 'new', project_id: '', notes: '' })
    }
  }, [editRow, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        full_name: form.full_name,
        mobile: form.mobile,
        email: form.email || undefined,
        source: form.source,
        stage: form.stage,
        project_id: form.project_id ? Number(form.project_id) : undefined,
        notes: form.notes || undefined,
      }
      if (editRow?.id) {
        await api.put(`/leads/${editRow.id}`, payload)
      } else {
        await api.post('/leads', payload)
      }
      qc.invalidateQueries({ queryKey: ['leads'] })
      qc.invalidateQueries({ queryKey: ['leads-kanban'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_lead') : t('add_lead')}>
      <form onSubmit={submit} className="space-y-4">
        <Input label={t('name')} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        <Input label={t('mobile')} value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} required />
        <Input label={t('email')} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <SelectField label={t('lead_source')} value={form.source} onChange={(v) => setForm({ ...form, source: v })} options={[
          { value: 'website', label: 'Website' },
          { value: 'facebook', label: 'Facebook' },
          { value: 'instagram', label: 'Instagram' },
          { value: 'referral', label: 'Referral' },
          { value: 'broker', label: 'Broker' },
          { value: 'walk_in', label: 'Walk In' },
        ]} />
        <SelectField label={t('projects')} value={form.project_id} onChange={(v) => setForm({ ...form, project_id: v })}
          options={projects.map((p) => ({ value: String(p.id), label: String(p.name_ar) }))} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function MaintenanceFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: units = [] } = useUnitsLookup()
  const { data: customers = [] } = useCustomersLookup()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ unit_id: '', customer_id: '', title: '', description: '', priority: 'medium', status: 'open' })

  useEffect(() => {
    if (editRow) {
      setForm({
        unit_id: String(editRow.unit_id ?? ''),
        customer_id: String(editRow.customer_id ?? ''),
        title: String(editRow.title ?? ''),
        description: String(editRow.description ?? ''),
        priority: String(editRow.priority ?? 'medium'),
        status: String(editRow.status ?? 'open'),
      })
    } else {
      setForm({ unit_id: '', customer_id: '', title: '', description: '', priority: 'medium', status: 'open' })
    }
  }, [editRow, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        unit_id: Number(form.unit_id),
        customer_id: form.customer_id ? Number(form.customer_id) : undefined,
        title: form.title,
        description: form.description || undefined,
        priority: form.priority,
      }
      if (editRow?.id) {
        await api.put(`/property/maintenance/${editRow.id}`, { ...payload, status: form.status })
      } else {
        await api.post('/property/maintenance', payload)
      }
      qc.invalidateQueries({ queryKey: ['maintenance'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_maintenance') : t('add_maintenance')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('units')} value={form.unit_id} onChange={(v) => setForm({ ...form, unit_id: v })} required
          options={units.map((u) => ({ value: String(u.id), label: u.unit_code }))} />
        <SelectField label={t('customers')} value={form.customer_id} onChange={(v) => setForm({ ...form, customer_id: v })}
          options={customers.map((c) => ({ value: String(c.id), label: c.full_name_ar }))} />
        <Input label={t('request')} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <Input label={t('description')} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <SelectField label="Priority" value={form.priority} onChange={(v) => setForm({ ...form, priority: v })} options={[
          { value: 'low', label: 'Low' }, { value: 'medium', label: 'Medium' }, { value: 'high', label: 'High' },
        ]} />
        {editRow && (
          <SelectField label={t('status')} value={form.status} onChange={(v) => setForm({ ...form, status: v })} options={[
            { value: 'open', label: 'Open' }, { value: 'in_progress', label: 'In Progress' }, { value: 'resolved', label: 'Resolved' },
          ]} />
        )}
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function TicketFormModal({ open, onClose, editRow }: ModalProps) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: customers = [] } = useCustomersLookup()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ customer_id: '', category: 'inquiry', subject: '', description: '', priority: 'medium', status: 'open' })

  useEffect(() => {
    if (editRow) {
      setForm({
        customer_id: String(editRow.customer_id ?? ''),
        category: String(editRow.category ?? 'inquiry'),
        subject: String(editRow.subject ?? ''),
        description: String(editRow.description ?? ''),
        priority: String(editRow.priority ?? 'medium'),
        status: String(editRow.status ?? 'open'),
      })
    } else {
      setForm({ customer_id: '', category: 'inquiry', subject: '', description: '', priority: 'medium', status: 'open' })
    }
  }, [editRow, open])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        customer_id: form.customer_id ? Number(form.customer_id) : undefined,
        category: form.category,
        subject: form.subject,
        description: form.description || undefined,
        priority: form.priority,
      }
      if (editRow?.id) {
        await api.put(`/tickets/${editRow.id}`, { ...payload, status: form.status })
      } else {
        await api.post('/tickets', payload)
      }
      qc.invalidateQueries({ queryKey: ['tickets'] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editRow ? t('edit_ticket') : t('add_ticket')}>
      <form onSubmit={submit} className="space-y-4">
        <SelectField label={t('customers')} value={form.customer_id} onChange={(v) => setForm({ ...form, customer_id: v })}
          options={customers.map((c) => ({ value: String(c.id), label: c.full_name_ar }))} />
        <SelectField label="Category" value={form.category} onChange={(v) => setForm({ ...form, category: v })} options={[
          { value: 'inquiry', label: 'Inquiry' }, { value: 'complaint', label: 'Complaint' }, { value: 'support', label: 'Support' },
        ]} />
        <Input label="Subject" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} required />
        <Input label={t('description')} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <SelectField label="Priority" value={form.priority} onChange={(v) => setForm({ ...form, priority: v })} options={[
          { value: 'low', label: 'Low' }, { value: 'medium', label: 'Medium' }, { value: 'high', label: 'High' },
        ]} />
        {editRow && (
          <SelectField label={t('status')} value={form.status} onChange={(v) => setForm({ ...form, status: v })} options={[
            { value: 'open', label: 'Open' }, { value: 'in_progress', label: 'In Progress' }, { value: 'resolved', label: 'Resolved' }, { value: 'closed', label: 'Closed' },
          ]} />
        )}
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
