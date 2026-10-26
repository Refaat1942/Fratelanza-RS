import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Receipt, Plus, CheckCircle2, XCircle, Wallet, Paperclip, Building2 } from 'lucide-react'
import api from '@/lib/api'
import { apiErrorMessage } from '@/lib/apiError'
import { openTenantFile } from '@/lib/files'
import { PageHeader } from '@/components/ui/PageHeader'
import { DataTable } from '@/components/ui/DataTable'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'
import { SelectField, TextAreaField, FormGrid, Tabs, ErrorNote, Badge } from '@/components/ui/FormFields'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { usePermissionsStore } from '@/stores/permissionsStore'

type Row = Record<string, unknown>
const today = () => new Date().toISOString().slice(0, 10)

async function uploadFile(file: File, category: string): Promise<string> {
  const body = new FormData()
  body.append('file', file)
  body.append('category', category)
  const { data } = await api.post<{ url: string }>('/files', body, { headers: { 'Content-Type': 'multipart/form-data' } })
  return data.url
}


function AttachmentInput({ category, value, onChange }: { category: string; value: string; onChange: (url: string) => void }) {
  const { t } = useTranslation()
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-slate-700">{t('re.fields.attachment')}</label>
      <input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" className="block w-full text-sm" disabled={uploading}
        onChange={async (e) => {
          const file = e.target.files?.[0]
          if (!file) return
          setUploading(true); setError(null)
          try { onChange(await uploadFile(file, category)) } catch (err) { setError(apiErrorMessage(err, t)) } finally { setUploading(false) }
        }} />
      {uploading && <p className="text-xs text-slate-500">{t('loading')}</p>}
      {value && <p className="text-xs text-emerald-700"><Paperclip className="me-1 inline h-3 w-3" />{t('re.uploaded')}</p>}
      <ErrorNote message={error} />
    </div>
  )
}

const PROPERTY_CATEGORIES = ['maintenance', 'plumbing', 'electrical', 'painting', 'cleaning', 'security', 'utilities', 'taxes', 'insurance', 'other']
const ADMIN_CATEGORIES = ['rent', 'utilities', 'salaries_other', 'marketing', 'office_supplies', 'transport', 'government_fees', 'professional_fees', 'software', 'other']

export function PropertyExpensesPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { formatEGP } = useFormatNumber()
  const can = usePermissionsStore((s) => s.can)
  const [tab, setTab] = useState('list')
  const [groupBy, setGroupBy] = useState('unit')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ unit_id: '', expense_date: today(), category: 'maintenance', amount: '', vendor: '', description: '', charged_to: 'owner', attachment_url: '' })
  const [fromMr, setFromMr] = useState<Row | null>(null)
  const [mrForm, setMrForm] = useState({ amount: '', expense_date: today(), vendor: '', charged_to: 'owner' })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const expenses = useQuery({ queryKey: ['property-expenses'], queryFn: async () => (await api.get<Row[]>('/property-expenses')).data })
  const summary = useQuery({ queryKey: ['property-expenses-summary', groupBy], queryFn: async () => (await api.get<Row[]>(`/property-expenses/summary?group_by=${groupBy}`)).data })
  const units = useQuery({ queryKey: ['rental-units'], enabled: can('rentals'), queryFn: async () => (await api.get<Row[]>('/rentals/units')).data })
  const unitsBoard = useQuery({
    queryKey: ['units-lookup', false], enabled: !can('rentals') && can('projects'),
    queryFn: async () => Object.values((await api.get<Record<string, Row[]>>('/projects/units/board')).data).flat(),
  })
  const maintenance = useQuery({ queryKey: ['maintenance'], enabled: can('property'), queryFn: async () => (await api.get<Row[]>('/property/maintenance')).data })
  const unitOptions = (units.data ?? unitsBoard.data ?? []).map((u) => ({ value: String(u.id), label: String(u.unit_code) }))
  const linked = new Set((expenses.data ?? []).map((e) => e.maintenance_request_id).filter(Boolean))
  const refresh = () => ['property-expenses', 'property-expenses-summary', 're-dashboard'].forEach((k) => qc.invalidateQueries({ queryKey: [k] }))

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError(null)
    try {
      await api.post('/property-expenses', { ...form, unit_id: Number(form.unit_id), amount: Number(form.amount), attachment_url: form.attachment_url || null })
      setOpen(false); refresh()
    } catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }
  const saveFromMr = async (e: React.FormEvent) => {
    e.preventDefault(); if (!fromMr) return
    setBusy(true); setError(null)
    try { await api.post(`/property-expenses/from-maintenance/${fromMr.id}`, { ...mrForm, amount: Number(mrForm.amount) }); setFromMr(null); refresh() }
    catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }
  const act = async (row: Row, path: string, body?: Row) => {
    try { await api.post(`/property-expenses/${row.id}/${path}`, body); refresh() } catch (err) { alert(apiErrorMessage(err, t)) }
  }

  return (
    <div>
      <PageHeader title={t('re.nav.property_expenses')} subtitle={t('re.expenses.subtitle')} icon={Receipt} accentIndex={3}
        actions={can('property_expenses', 'create') ? <Button onClick={() => { setError(null); setOpen(true) }}><Plus className="me-2 h-4 w-4" />{t('re.expenses.new')}</Button> : undefined} />
      <Tabs active={tab} onChange={setTab} tabs={[
        { key: 'list', label: t('re.expenses.tab_list') },
        { key: 'summary', label: t('re.expenses.tab_summary') },
        ...(can('property') ? [{ key: 'maintenance', label: t('re.expenses.tab_maintenance') }] : []),
      ]} />
      {tab === 'list' && (
        <DataTable title={t('re.expenses.tab_list')} loading={expenses.isLoading} data={expenses.data ?? []} exportFilename={can('property_expenses', 'export') ? 'property-expenses' : undefined}
          columns={[
            { key: 'expense_date', label: t('re.fields.date') },
            { key: 'unit_code', label: t('re.fields.unit') },
            { key: 'owner_name', label: t('re.fields.owner'), render: (r) => String(r.owner_name ?? '—') },
            { key: 'category', label: t('re.fields.category'), render: (r) => t(`re.expense_category.${r.category}`, { defaultValue: String(r.category) }) },
            { key: 'amount', label: t('re.fields.amount'), render: (r) => formatEGP(r.amount as number) },
            { key: 'charged_to', label: t('re.fields.charged_to'), render: (r) => t(`re.charged_to.${r.charged_to}`) },
            { key: 'approval_status', label: t('re.fields.approval'), render: (r) => <Badge tone={r.approval_status === 'approved' ? 'green' : r.approval_status === 'rejected' ? 'red' : 'amber'}>{t(`re.status.${r.approval_status}`)}</Badge> },
            { key: 'payment_status', label: t('re.fields.payment'), render: (r) => <Badge tone={r.payment_status === 'paid' ? 'green' : 'slate'}>{t(`re.status.${r.payment_status}`)}</Badge> },
          ]}
          rowActions={(row) => (
            <div className="flex flex-wrap gap-1">
              {row.approval_status === 'pending' && can('property_expenses', 'approve') && <>
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => act(row, 'approve')}><CheckCircle2 className="me-1 h-3.5 w-3.5" />{t('re.approve')}</Button>
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs text-red-600" onClick={() => act(row, 'reject')}><XCircle className="me-1 h-3.5 w-3.5" />{t('re.reject')}</Button>
              </>}
              {row.approval_status === 'approved' && row.payment_status !== 'paid' && can('property_expenses', 'create') && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => act(row, 'mark-paid', { paid_on: today() })}><Wallet className="me-1 h-3.5 w-3.5" />{t('re.expenses.mark_paid')}</Button>
              )}
              {row.attachment_url ? <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openTenantFile(String(row.attachment_url))}><Paperclip className="h-3.5 w-3.5" /></Button> : null}
            </div>
          )}
        />
      )}
      {tab === 'summary' && (
        <Card>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            {['unit', 'owner', 'month', 'category'].map((g) => (
              <Button key={g} variant={groupBy === g ? 'primary' : 'secondary'} onClick={() => setGroupBy(g)}>{t(`re.expenses.by_${g}`)}</Button>
            ))}
          </div>
          <ul className="divide-y divide-slate-100">
            {(summary.data ?? []).map((r) => (
              <li key={String(r.group)} className="flex items-center justify-between py-2 text-sm">
                <span>{groupBy === 'category' ? t(`re.expense_category.${r.group}`, { defaultValue: String(r.group) }) : String(r.group)} <span className="text-slate-400">({String(r.count)})</span></span>
                <span className="font-semibold">{formatEGP(r.total as number)}</span>
              </li>
            ))}
            {!summary.data?.length && <li className="py-6 text-center text-slate-500">{t('no_data')}</li>}
          </ul>
        </Card>
      )}
      {tab === 'maintenance' && (
        <DataTable title={t('re.expenses.tab_maintenance')} loading={maintenance.isLoading} data={maintenance.data ?? []}
          columns={[
            { key: 'title', label: t('request') },
            { key: 'unit_code', label: t('re.fields.unit') },
            { key: 'status', label: t('status') },
            { key: 'id', label: t('re.expenses.linked_expense'), render: (r) => (linked.has(r.id) ? <Badge tone="green">{t('re.expenses.linked')}</Badge> : <Badge>{t('re.expenses.not_linked')}</Badge>) },
          ]}
          rowActions={(row) => (!linked.has(row.id) && can('property_expenses', 'create') ? (
            <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => { setError(null); setMrForm({ amount: '', expense_date: today(), vendor: '', charged_to: 'owner' }); setFromMr(row) }}>
              <Building2 className="me-1 h-3.5 w-3.5" />{t('re.expenses.record_cost')}
            </Button>
          ) : null)}
        />
      )}
      <Modal open={open} onClose={() => setOpen(false)} title={t('re.expenses.new')} className="max-w-2xl">
        <form onSubmit={save} className="space-y-4">
          <ErrorNote message={error} />
          <FormGrid>
            <SelectField label={t('re.fields.unit')} value={form.unit_id} onChange={(v) => setForm({ ...form, unit_id: v })} required options={unitOptions} />
            <Input type="date" label={t('re.fields.date')} value={form.expense_date} onChange={(e) => setForm({ ...form, expense_date: e.target.value })} required />
            <SelectField label={t('re.fields.category')} value={form.category} onChange={(v) => setForm({ ...form, category: v })} required options={PROPERTY_CATEGORIES.map((c) => ({ value: c, label: t(`re.expense_category.${c}`) }))} />
            <Input type="number" min="0.01" step="0.01" label={t('re.fields.amount')} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
            <Input label={t('re.fields.vendor')} value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value })} />
            <SelectField label={t('re.fields.charged_to')} value={form.charged_to} onChange={(v) => setForm({ ...form, charged_to: v })} required options={['owner', 'company'].map((c) => ({ value: c, label: t(`re.charged_to.${c}`) }))} />
          </FormGrid>
          <TextAreaField label={t('description')} value={form.description} onChange={(v) => setForm({ ...form, description: v })} rows={2} />
          <AttachmentInput category="expenses" value={form.attachment_url} onChange={(url) => setForm({ ...form, attachment_url: url })} />
          <div className="flex gap-3"><Button type="submit" loading={busy}>{t('save')}</Button><Button type="button" variant="secondary" onClick={() => setOpen(false)}>{t('cancel')}</Button></div>
        </form>
      </Modal>
      <Modal open={!!fromMr} onClose={() => setFromMr(null)} title={t('re.expenses.record_cost')}>
        <form onSubmit={saveFromMr} className="space-y-4">
          <ErrorNote message={error} />
          <p className="text-sm text-slate-600">{String(fromMr?.title ?? '')} — {String(fromMr?.unit_code ?? '')}</p>
          <Input type="number" min="0.01" step="0.01" label={t('re.fields.amount')} value={mrForm.amount} onChange={(e) => setMrForm({ ...mrForm, amount: e.target.value })} required />
          <Input type="date" label={t('re.fields.date')} value={mrForm.expense_date} onChange={(e) => setMrForm({ ...mrForm, expense_date: e.target.value })} required />
          <Input label={t('re.fields.vendor')} value={mrForm.vendor} onChange={(e) => setMrForm({ ...mrForm, vendor: e.target.value })} />
          <SelectField label={t('re.fields.charged_to')} value={mrForm.charged_to} onChange={(v) => setMrForm({ ...mrForm, charged_to: v })} options={['owner', 'company'].map((c) => ({ value: c, label: t(`re.charged_to.${c}`) }))} />
          <div className="flex gap-3"><Button type="submit" loading={busy}>{t('save')}</Button><Button type="button" variant="secondary" onClick={() => setFromMr(null)}>{t('cancel')}</Button></div>
        </form>
      </Modal>
    </div>
  )
}

export function AdminExpensesPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { formatEGP } = useFormatNumber()
  const can = usePermissionsStore((s) => s.can)
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ category: 'rent', expense_date: today(), amount: '', description: '', vendor: '', document_url: '' })
  const [payRow, setPayRow] = useState<Row | null>(null)
  const [payForm, setPayForm] = useState({ amount: '', paid_on: today() })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const list = useQuery({ queryKey: ['admin-expenses'], queryFn: async () => (await api.get<Row[]>('/admin-expenses')).data })
  const summary = useQuery({ queryKey: ['admin-expenses-summary'], queryFn: async () => (await api.get<{ by_month: Row[]; by_category: Row[]; unpaid: number }>('/admin-expenses/summary')).data })
  const refresh = () => ['admin-expenses', 'admin-expenses-summary', 're-dashboard'].forEach((k) => qc.invalidateQueries({ queryKey: [k] }))

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError(null)
    try { await api.post('/admin-expenses', { ...form, amount: Number(form.amount), document_url: form.document_url || null }); setOpen(false); refresh() }
    catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }
  const pay = async (e: React.FormEvent) => {
    e.preventDefault(); if (!payRow) return
    setBusy(true); setError(null)
    try { await api.post(`/admin-expenses/${payRow.id}/payments`, { amount: Number(payForm.amount), paid_on: payForm.paid_on }); setPayRow(null); refresh() }
    catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }

  return (
    <div>
      <PageHeader title={t('re.nav.admin_expenses')} subtitle={t('re.admin_expenses.subtitle')} icon={Receipt} accentIndex={1}
        actions={can('admin_expenses', 'create') ? <Button onClick={() => { setError(null); setOpen(true) }}><Plus className="me-2 h-4 w-4" />{t('re.admin_expenses.new')}</Button> : undefined} />
      <div className="mb-6 grid gap-4 md:grid-cols-3">
        <Card><p className="text-sm text-slate-500">{t('re.admin_expenses.unpaid')}</p><p className="mt-2 text-2xl font-bold">{formatEGP(summary.data?.unpaid)}</p></Card>
        <Card className="md:col-span-2">
          <p className="mb-2 text-sm text-slate-500">{t('re.admin_expenses.by_category')}</p>
          <div className="flex flex-wrap gap-2">{(summary.data?.by_category ?? []).map((c) => (
            <Badge key={String(c.category)} tone="blue">{t(`re.admin_category.${c.category}`, { defaultValue: String(c.category) })}: {formatEGP(c.total as number)}</Badge>
          ))}</div>
        </Card>
      </div>
      <DataTable title={t('re.nav.admin_expenses')} loading={list.isLoading} data={list.data ?? []} exportFilename={can('admin_expenses', 'export') ? 'admin-expenses' : undefined}
        columns={[
          { key: 'expense_date', label: t('re.fields.date') },
          { key: 'category', label: t('re.fields.category'), render: (r) => t(`re.admin_category.${r.category}`, { defaultValue: String(r.category) }) },
          { key: 'description', label: t('description'), render: (r) => String(r.description ?? '—') },
          { key: 'amount', label: t('re.fields.amount'), render: (r) => formatEGP(r.amount as number) },
          { key: 'amount_paid', label: t('re.fields.paid'), render: (r) => formatEGP(r.amount_paid as number) },
          { key: 'remaining', label: t('re.fields.remaining'), render: (r) => formatEGP(r.remaining as number) },
          { key: 'payment_status', label: t('status'), render: (r) => <Badge tone={r.payment_status === 'paid' ? 'green' : r.payment_status === 'partial' ? 'amber' : 'slate'}>{t(`re.status.${r.payment_status}`)}</Badge> },
        ]}
        rowActions={(row) => (
          <div className="flex gap-1">
            {(row.remaining as number) > 0 && can('admin_expenses', 'collect') && (
              <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => { setError(null); setPayForm({ amount: String(row.remaining), paid_on: today() }); setPayRow(row) }}><Wallet className="me-1 h-3.5 w-3.5" />{t('re.admin_expenses.pay')}</Button>
            )}
            {row.document_url ? <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openTenantFile(String(row.document_url))}><Paperclip className="h-3.5 w-3.5" /></Button> : null}
          </div>
        )}
      />
      <Modal open={open} onClose={() => setOpen(false)} title={t('re.admin_expenses.new')}>
        <form onSubmit={save} className="space-y-4">
          <ErrorNote message={error} />
          <SelectField label={t('re.fields.category')} value={form.category} onChange={(v) => setForm({ ...form, category: v })} required options={ADMIN_CATEGORIES.map((c) => ({ value: c, label: t(`re.admin_category.${c}`) }))} />
          <Input type="date" label={t('re.fields.date')} value={form.expense_date} onChange={(e) => setForm({ ...form, expense_date: e.target.value })} required />
          <Input type="number" min="0.01" step="0.01" label={t('re.fields.amount')} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          <Input label={t('re.fields.vendor')} value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value })} />
          <TextAreaField label={t('description')} value={form.description} onChange={(v) => setForm({ ...form, description: v })} rows={2} />
          <AttachmentInput category="admin_expenses" value={form.document_url} onChange={(url) => setForm({ ...form, document_url: url })} />
          <div className="flex gap-3"><Button type="submit" loading={busy}>{t('save')}</Button><Button type="button" variant="secondary" onClick={() => setOpen(false)}>{t('cancel')}</Button></div>
        </form>
      </Modal>
      <Modal open={!!payRow} onClose={() => setPayRow(null)} title={t('re.admin_expenses.pay')}>
        <form onSubmit={pay} className="space-y-4">
          <ErrorNote message={error} />
          <Input type="number" min="0.01" step="0.01" label={t('re.fields.amount')} value={payForm.amount} onChange={(e) => setPayForm({ ...payForm, amount: e.target.value })} required />
          <Input type="date" label={t('re.fields.date')} value={payForm.paid_on} onChange={(e) => setPayForm({ ...payForm, paid_on: e.target.value })} required />
          <div className="flex gap-3"><Button type="submit" loading={busy}>{t('re.confirm')}</Button><Button type="button" variant="secondary" onClick={() => setPayRow(null)}>{t('cancel')}</Button></div>
        </form>
      </Modal>
    </div>
  )
}
