import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Home, Plus, FileSignature, RefreshCcw, Ban, Wallet, Undo2, BadgePercent, Eye, CheckCircle2, Users } from 'lucide-react'
import api from '@/lib/api'
import { apiErrorMessage } from '@/lib/apiError'
import { PageHeader } from '@/components/ui/PageHeader'
import { DataTable } from '@/components/ui/DataTable'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StatCard } from '@/components/ui/StatCard'
import { SelectField, TextAreaField, FormGrid, Tabs, ErrorNote, Badge } from '@/components/ui/FormFields'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { usePermissionsStore } from '@/stores/permissionsStore'

type Row = Record<string, unknown>
const today = () => new Date().toISOString().slice(0, 10)

const STATUS_TONE: Record<string, 'green' | 'amber' | 'red' | 'slate' | 'blue' | 'violet'> = {
  active: 'green', expiring: 'amber', expired: 'red', terminated: 'slate', renewed: 'violet', draft: 'blue',
  paid: 'green', partial: 'amber', pending: 'blue', overdue: 'red', waived: 'violet', cancelled: 'slate',
}

export function StatusBadge({ value }: { value: unknown }) {
  const { t } = useTranslation()
  const v = String(value ?? '')
  return <Badge tone={STATUS_TONE[v] ?? 'slate'}>{t(`re.status.${v}`, { defaultValue: v })}</Badge>
}

function useUnits() {
  return useQuery({ queryKey: ['rental-units'], queryFn: async () => (await api.get<Row[]>('/rentals/units')).data })
}

function useOwners(enabled: boolean) {
  return useQuery({
    queryKey: ['owners'], enabled,
    queryFn: async () => (await api.get<Row[]>('/owners')).data,
  })
}

const emptyContract = {
  unit_id: '', owner_id: '', tenant_name: '', tenant_mobile: '', tenant_id_number: '', start_date: today(), end_date: '',
  rent_amount: '', payment_frequency: 'monthly', deposit_amount: '0', other_charges: '0', payment_terms: '', notes: '', activate: true,
}

function ContractFormModal({ open, onClose, fixedUnitId, title, onSubmit }: {
  open: boolean; onClose: () => void; fixedUnitId?: number; title: string
  onSubmit: (payload: Row) => Promise<void>
}) {
  const { t } = useTranslation()
  const can = usePermissionsStore((s) => s.can)
  const { data: units = [] } = useUnits()
  const { data: owners = [] } = useOwners(can('owners'))
  const [form, setForm] = useState({ ...emptyContract, unit_id: fixedUnitId ? String(fixedUnitId) : '' })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const set = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (form.end_date && form.end_date <= form.start_date) { setError(t('re.errors.end_before_start')); return }
    setLoading(true)
    try {
      await onSubmit({
        unit_id: Number(form.unit_id), owner_id: form.owner_id ? Number(form.owner_id) : null,
        tenant_name: form.tenant_name, tenant_mobile: form.tenant_mobile || null, tenant_id_number: form.tenant_id_number || null,
        start_date: form.start_date, end_date: form.end_date, rent_amount: Number(form.rent_amount),
        payment_frequency: form.payment_frequency, deposit_amount: Number(form.deposit_amount || 0),
        other_charges: Number(form.other_charges || 0), payment_terms: form.payment_terms || null, notes: form.notes || null,
        activate: form.activate,
      })
      setForm({ ...emptyContract, unit_id: fixedUnitId ? String(fixedUnitId) : '' })
      onClose()
    } catch (err) {
      setError(apiErrorMessage(err, t))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={title} className="max-w-2xl">
      <form onSubmit={submit} className="space-y-4">
        <ErrorNote message={error} />
        <FormGrid>
          <SelectField label={t('re.fields.unit')} value={form.unit_id} onChange={(v) => set('unit_id', v)} required disabled={!!fixedUnitId}
            options={units.map((u) => ({ value: String(u.id), label: `${u.unit_code} — ${t(`re.occupancy.${u.occupancy_status}`)}` }))} />
          {can('owners') && (
            <SelectField label={t('re.fields.owner')} value={form.owner_id} onChange={(v) => set('owner_id', v)}
              placeholder={t('re.fields.owner_from_unit')} options={owners.map((o) => ({ value: String(o.id), label: String(o.full_name) }))} />
          )}
          <Input label={t('re.fields.tenant_name')} value={form.tenant_name} onChange={(e) => set('tenant_name', e.target.value)} required />
          <Input label={t('re.fields.tenant_mobile')} value={form.tenant_mobile} onChange={(e) => set('tenant_mobile', e.target.value)} dir="ltr" />
          <Input label={t('re.fields.tenant_id_number')} value={form.tenant_id_number} onChange={(e) => set('tenant_id_number', e.target.value)} dir="ltr" />
          <SelectField label={t('re.fields.payment_frequency')} value={form.payment_frequency} onChange={(v) => set('payment_frequency', v)} required
            options={['monthly', 'quarterly', 'semiannual', 'annual'].map((f) => ({ value: f, label: t(`re.freq.${f}`) }))} />
          <Input type="date" label={t('re.fields.start_date')} value={form.start_date} onChange={(e) => set('start_date', e.target.value)} required />
          <Input type="date" label={t('re.fields.end_date')} value={form.end_date} onChange={(e) => set('end_date', e.target.value)} required />
          <Input type="number" min="1" step="0.01" label={t('re.fields.monthly_rent')} value={form.rent_amount} onChange={(e) => set('rent_amount', e.target.value)} required />
          <Input type="number" min="0" step="0.01" label={t('re.fields.deposit')} value={form.deposit_amount} onChange={(e) => set('deposit_amount', e.target.value)} />
          <Input type="number" min="0" step="0.01" label={t('re.fields.other_charges')} value={form.other_charges} onChange={(e) => set('other_charges', e.target.value)} />
        </FormGrid>
        <TextAreaField label={t('re.fields.payment_terms')} value={form.payment_terms} onChange={(v) => set('payment_terms', v)} rows={2} />
        <TextAreaField label={t('re.fields.notes')} value={form.notes} onChange={(v) => set('notes', v)} rows={2} />
        {can('rentals', 'approve') && (
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={form.activate} onChange={(e) => set('activate', e.target.checked)} />
            {t('re.rentals.activate_now')}
          </label>
        )}
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>{t('save')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

function ActionModal({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: React.ReactNode }) {
  return <Modal open={open} onClose={onClose} title={title}>{children}</Modal>
}

function ContractDetail({ id, onClose }: { id: number | null; onClose: () => void }) {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const { data } = useQuery({
    queryKey: ['rental-contract', id], enabled: !!id,
    queryFn: async () => (await api.get<Row & { receivables: Row[]; renewal_history: Row[]; unit_tenant_history: Row[] }>(`/rentals/contracts/${id}`)).data,
  })
  return (
    <Modal open={!!id} onClose={onClose} title={t('re.rentals.contract_details')} className="max-w-3xl">
      {!data ? <p className="text-slate-500">{t('loading')}</p> : (
        <div className="space-y-5 text-sm">
          <div className="grid gap-3 sm:grid-cols-3">
            <Info label={t('re.fields.contract_number')} value={String(data.contract_number)} />
            <Info label={t('re.fields.unit')} value={String(data.unit_code)} />
            <Info label={t('status')} value={<StatusBadge value={data.status} />} />
            <Info label={t('re.fields.tenant_name')} value={String(data.tenant_name)} />
            <Info label={t('re.fields.tenant_id_number')} value={String(data.tenant_id_number ?? '—')} />
            <Info label={t('re.fields.owner')} value={String(data.owner_name ?? '—')} />
            <Info label={t('re.fields.period')} value={`${data.start_date} → ${data.end_date}`} />
            <Info label={t('re.fields.monthly_rent')} value={formatEGP(data.rent_amount as number)} />
            <Info label={t('re.fields.total_value')} value={formatEGP(data.total_value as number)} />
            <Info label={t('re.fields.collected')} value={formatEGP(data.collected as number)} />
            <Info label={t('re.fields.outstanding')} value={formatEGP(data.outstanding as number)} />
            {data.termination_reason ? <Info label={t('re.fields.termination_reason')} value={`${data.termination_date} — ${data.termination_reason}`} /> : null}
          </div>
          <section>
            <h4 className="mb-2 font-semibold text-slate-800">{t('re.rentals.schedule')}</h4>
            <div className="max-h-64 overflow-auto rounded-lg border border-slate-200">
              <table className="w-full text-xs">
                <thead className="bg-slate-50"><tr>
                  <th className="p-2 text-start">{t('re.fields.period')}</th><th className="p-2 text-start">{t('re.fields.due_date')}</th>
                  <th className="p-2 text-start">{t('re.fields.amount_due')}</th><th className="p-2 text-start">{t('re.fields.paid')}</th>
                  <th className="p-2 text-start">{t('status')}</th>
                </tr></thead>
                <tbody>{data.receivables.map((r) => (
                  <tr key={String(r.id)} className="border-t border-slate-100">
                    <td className="p-2">{String(r.period_start)} → {String(r.period_end)}</td><td className="p-2">{String(r.due_date)}</td>
                    <td className="p-2">{formatEGP(r.amount_due as number)}</td><td className="p-2">{formatEGP(r.amount_paid as number)}</td>
                    <td className="p-2"><StatusBadge value={r.status} /></td>
                  </tr>))}</tbody>
              </table>
            </div>
          </section>
          <section>
            <h4 className="mb-2 font-semibold text-slate-800">{t('re.rentals.unit_history')}</h4>
            <ul className="space-y-1">{data.unit_tenant_history.map((h) => (
              <li key={String(h.id)} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2">
                <span>{String(h.contract_number)} — {String(h.tenant_name)}</span>
                <span className="text-slate-500">{String(h.start_date)} → {String(h.end_date)} · {formatEGP(h.rent_amount as number)}</span>
                <StatusBadge value={h.status} />
              </li>))}</ul>
          </section>
        </div>
      )}
    </Modal>
  )
}

function Info({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><div className="mt-1 font-medium text-slate-900">{value}</div></div>
}

export function RentalsPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { formatEGP, formatInteger } = useFormatNumber()
  const can = usePermissionsStore((s) => s.can)
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') ?? 'contracts'
  const statusFilter = params.get('status') ?? ''
  const [createOpen, setCreateOpen] = useState(false)
  const [detailId, setDetailId] = useState<number | null>(null)
  const [action, setAction] = useState<{ kind: string; row: Row } | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const contracts = useQuery({ queryKey: ['rental-contracts'], queryFn: async () => (await api.get<Row[]>('/rentals/contracts')).data })
  const receivables = useQuery({ queryKey: ['rent-receivables'], queryFn: async () => (await api.get<Row[]>('/rentals/receivables')).data })
  const summary = useQuery({ queryKey: ['rentals-summary'], queryFn: async () => (await api.get<Row>('/rentals/summary')).data })
  const units = useUnits()

  const refresh = () => {
    for (const key of ['rental-contracts', 'rent-receivables', 'rentals-summary', 'rental-units', 'rental-contract', 're-dashboard']) {
      qc.invalidateQueries({ queryKey: [key] })
    }
  }

  const contractRows = useMemo(() => (contracts.data ?? []).filter((c) => !statusFilter || c.status === statusFilter), [contracts.data, statusFilter])
  const receivableRows = useMemo(() => (receivables.data ?? []).filter((r) => !statusFilter || r.status === statusFilter), [receivables.data, statusFilter])

  const openAction = (kind: string, row: Row, defaults: Record<string, string> = {}) => {
    setError(null)
    setForm(defaults)
    setAction({ kind, row })
  }

  const runAction = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!action) return
    setBusy(true)
    setError(null)
    const id = action.row.id
    try {
      if (action.kind === 'terminate') await api.post(`/rentals/contracts/${id}/terminate`, { termination_date: form.date, reason: form.reason })
      if (action.kind === 'renew') await api.post(`/rentals/contracts/${id}/renew`, { new_end_date: form.end_date, new_rent_amount: form.rent ? Number(form.rent) : null })
      if (action.kind === 'pay') await api.post(`/rentals/receivables/${id}/payments`, { amount: Number(form.amount), paid_on: form.date, method: form.method || 'cash', receipt_reference: form.reference || null })
      if (action.kind === 'refund') await api.post(`/rentals/receivables/${id}/refunds`, { amount: Number(form.amount), paid_on: form.date, notes: form.reason || null })
      if (action.kind === 'waive') await api.post(`/rentals/receivables/${id}/adjustments`, { amount: Number(form.amount), reason: form.reason })
      setAction(null)
      refresh()
    } catch (err) {
      setError(apiErrorMessage(err, t))
    } finally {
      setBusy(false)
    }
  }

  const activate = async (row: Row) => {
    try { await api.post(`/rentals/contracts/${row.id}/approve`); refresh() } catch (err) { alert(apiErrorMessage(err, t)) }
  }

  const setTab = (key: string) => setParams((p) => { p.set('tab', key); p.delete('status'); return p })
  const statusOptions = tab === 'receivables'
    ? ['pending', 'partial', 'overdue', 'paid', 'waived', 'cancelled']
    : ['draft', 'active', 'expiring', 'expired', 'terminated', 'renewed']

  return (
    <div>
      <PageHeader
        title={t('re.nav.rentals')}
        subtitle={t('re.rentals.subtitle')}
        icon={Home}
        accentIndex={2}
        actions={can('rentals', 'create') ? (
          <Button onClick={() => setCreateOpen(true)}><Plus className="me-2 h-4 w-4" />{t('re.rentals.new_contract')}</Button>
        ) : undefined}
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title={t('re.cards.active_contracts')} value={formatInteger(summary.data?.active as number)} icon={FileSignature} />
        <StatCard title={t('re.cards.expiring_contracts')} value={formatInteger(summary.data?.expiring as number)} icon={RefreshCcw} color="amber" />
        <StatCard title={t('re.fields.outstanding')} value={formatEGP(summary.data?.outstanding as number)} icon={Wallet} color="sky" />
        <StatCard title={t('re.cards.overdue_rent')} value={formatEGP(summary.data?.overdue as number)} icon={Ban} color="rose" />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs active={tab} onChange={setTab} tabs={[
          { key: 'contracts', label: t('re.rentals.tab_contracts') },
          { key: 'receivables', label: t('re.rentals.tab_receivables') },
          { key: 'units', label: t('re.rentals.tab_units') },
        ]} />
        {tab !== 'units' && (
          <select className="input-field mb-4 max-w-[12rem]" value={statusFilter} aria-label={t('status')}
            onChange={(e) => setParams((p) => { if (e.target.value) { p.set('status', e.target.value) } else { p.delete('status') } return p })}>
            <option value="">{t('re.all_statuses')}</option>
            {statusOptions.map((s) => <option key={s} value={s}>{t(`re.status.${s}`)}</option>)}
          </select>
        )}
      </div>

      {tab === 'contracts' && (
        <DataTable title={t('re.rentals.tab_contracts')} loading={contracts.isLoading} data={contractRows} exportFilename={can('rentals', 'export') ? 'rental-contracts' : undefined}
          onEmptyAction={can('rentals', 'create') ? () => setCreateOpen(true) : undefined}
          columns={[
            { key: 'contract_number', label: t('re.fields.contract_number') },
            { key: 'unit_code', label: t('re.fields.unit') },
            { key: 'tenant_name', label: t('re.fields.tenant_name') },
            { key: 'start_date', label: t('re.fields.start_date') },
            { key: 'end_date', label: t('re.fields.end_date') },
            { key: 'rent_amount', label: t('re.fields.monthly_rent'), render: (r) => formatEGP(r.rent_amount as number) },
            { key: 'outstanding', label: t('re.fields.outstanding'), render: (r) => formatEGP(r.outstanding as number) },
            { key: 'status', label: t('status'), render: (r) => <StatusBadge value={r.status} /> },
          ]}
          rowActions={(row) => (
            <div className="flex flex-wrap gap-1">
              <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => setDetailId(row.id as number)}><Eye className="me-1 h-3.5 w-3.5" />{t('re.view')}</Button>
              {row.stored_status === 'draft' && can('rentals', 'approve') && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => activate(row)}><CheckCircle2 className="me-1 h-3.5 w-3.5" />{t('re.rentals.activate')}</Button>
              )}
              {row.stored_status === 'active' && can('rentals', 'create') && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openAction('renew', row, { end_date: '', rent: String(row.rent_amount) })}><RefreshCcw className="me-1 h-3.5 w-3.5" />{t('re.rentals.renew')}</Button>
              )}
              {row.stored_status === 'active' && can('rentals', 'terminate') && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs text-red-600" onClick={() => openAction('terminate', row, { date: today(), reason: '' })}><Ban className="me-1 h-3.5 w-3.5" />{t('re.rentals.terminate')}</Button>
              )}
            </div>
          )}
        />
      )}

      {tab === 'receivables' && (
        <DataTable title={t('re.rentals.tab_receivables')} loading={receivables.isLoading} data={receivableRows} exportFilename={can('rentals', 'export') ? 'rent-receivables' : undefined}
          columns={[
            { key: 'contract_number', label: t('re.fields.contract_number') },
            { key: 'tenant_name', label: t('re.fields.tenant_name') },
            { key: 'unit_code', label: t('re.fields.unit') },
            { key: 'due_date', label: t('re.fields.due_date') },
            { key: 'amount_due', label: t('re.fields.amount_due'), render: (r) => formatEGP(r.amount_due as number) },
            { key: 'amount_paid', label: t('re.fields.paid'), render: (r) => formatEGP(r.amount_paid as number) },
            { key: 'outstanding', label: t('re.fields.outstanding'), render: (r) => formatEGP(r.outstanding as number) },
            { key: 'overdue_days', label: t('re.fields.overdue_days'), render: (r) => (r.overdue_days ? formatInteger(r.overdue_days as number) : '—') },
            { key: 'status', label: t('status'), render: (r) => <StatusBadge value={r.status} /> },
          ]}
          rowActions={(row) => (
            <div className="flex flex-wrap gap-1">
              {(row.outstanding as number) > 0 && can('rentals', 'collect') && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openAction('pay', row, { amount: String(row.outstanding), date: today(), method: 'cash' })}><Wallet className="me-1 h-3.5 w-3.5" />{t('re.rentals.collect')}</Button>
              )}
              {(row.outstanding as number) > 0 && can('rentals', 'approve') && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openAction('waive', row, { amount: '', reason: '' })}><BadgePercent className="me-1 h-3.5 w-3.5" />{t('re.rentals.waive')}</Button>
              )}
              {(row.amount_paid as number) > 0 && can('rentals', 'refund') && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openAction('refund', row, { amount: '', date: today(), reason: '' })}><Undo2 className="me-1 h-3.5 w-3.5" />{t('re.rentals.refund')}</Button>
              )}
            </div>
          )}
        />
      )}

      {tab === 'units' && (
        <DataTable title={t('re.rentals.tab_units')} loading={units.isLoading} data={units.data ?? []}
          columns={[
            { key: 'unit_code', label: t('re.fields.unit') },
            { key: 'project_name', label: t('projects') },
            { key: 'unit_type', label: t('re.fields.property_type'), render: (r) => t(`re.unit_type.${r.unit_type}`, { defaultValue: String(r.unit_type) }) },
            { key: 'owner_name', label: t('re.fields.owner'), render: (r) => String(r.owner_name ?? '—') },
            { key: 'rental_category', label: t('re.fields.rental_category'), render: (r) => (r.rental_category ? t(`re.rental_category.${r.rental_category}`) : '—') },
            { key: 'furnishing_status', label: t('re.fields.furnishing'), render: (r) => (r.furnishing_status ? t(`re.furnishing.${r.furnishing_status}`) : '—') },
            { key: 'electricity_meter', label: t('re.fields.meters'), render: (r) => [r.electricity_meter, r.water_meter, r.gas_meter].filter(Boolean).join(' · ') || '—' },
            { key: 'current_tenant', label: t('re.fields.tenant_name'), render: (r) => String(r.current_tenant ?? '—') },
            { key: 'occupancy_status', label: t('re.fields.occupancy'), render: (r) => <Badge tone={r.occupancy_status === 'occupied' ? 'green' : 'blue'}><Users className="me-1 h-3 w-3" />{t(`re.occupancy.${r.occupancy_status}`)}</Badge> },
          ]}
        />
      )}

      <ContractFormModal open={createOpen} onClose={() => setCreateOpen(false)} title={t('re.rentals.new_contract')}
        onSubmit={async (payload) => { await api.post('/rentals/contracts', payload); refresh() }} />
      <ContractDetail id={detailId} onClose={() => setDetailId(null)} />

      <ActionModal open={!!action} onClose={() => setAction(null)} title={action ? t(`re.rentals.action_${action.kind}`) : ''}>
        <form onSubmit={runAction} className="space-y-4">
          <ErrorNote message={error} />
          {action && (action.kind === 'pay' || action.kind === 'refund' || action.kind === 'waive') && (
            <p className="text-sm text-slate-600">{String(action.row.contract_number)} — {String(action.row.tenant_name)} · {t('re.fields.outstanding')}: {formatEGP(action.row.outstanding as number)}</p>
          )}
          {action?.kind === 'terminate' && (<>
            <Input type="date" label={t('re.fields.termination_date')} value={form.date ?? ''} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
            <TextAreaField label={t('re.fields.termination_reason')} value={form.reason ?? ''} onChange={(v) => setForm({ ...form, reason: v })} required />
          </>)}
          {action?.kind === 'renew' && (<>
            <p className="text-sm text-slate-600">{t('re.rentals.renew_help', { end: String(action.row.end_date) })}</p>
            <Input type="date" label={t('re.fields.new_end_date')} value={form.end_date ?? ''} onChange={(e) => setForm({ ...form, end_date: e.target.value })} required />
            <Input type="number" min="1" step="0.01" label={t('re.fields.new_monthly_rent')} value={form.rent ?? ''} onChange={(e) => setForm({ ...form, rent: e.target.value })} />
          </>)}
          {(action?.kind === 'pay' || action?.kind === 'refund' || action?.kind === 'waive') && (
            <Input type="number" min="0.01" step="0.01" label={t('re.fields.amount')} value={form.amount ?? ''} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          )}
          {(action?.kind === 'pay' || action?.kind === 'refund') && (
            <Input type="date" label={t('re.fields.date')} value={form.date ?? ''} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
          )}
          {action?.kind === 'pay' && (<>
            <SelectField label={t('re.fields.method')} value={form.method ?? 'cash'} onChange={(v) => setForm({ ...form, method: v })}
              options={['cash', 'bank_transfer', 'cheque', 'instapay', 'card'].map((m) => ({ value: m, label: t(`re.method.${m}`) }))} />
            <Input label={t('re.fields.receipt_reference')} value={form.reference ?? ''} onChange={(e) => setForm({ ...form, reference: e.target.value })} />
          </>)}
          {(action?.kind === 'waive' || action?.kind === 'refund') && (
            <TextAreaField label={t('re.fields.reason')} value={form.reason ?? ''} onChange={(v) => setForm({ ...form, reason: v })} required={action?.kind === 'waive'} />
          )}
          <div className="flex gap-3 pt-2">
            <Button type="submit" loading={busy}>{t('re.confirm')}</Button>
            <Button type="button" variant="secondary" onClick={() => setAction(null)}>{t('cancel')}</Button>
          </div>
        </form>
      </ActionModal>
    </div>
  )
}
