import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Landmark, Plus, Calculator, CheckCircle2, Wallet, Printer, XCircle } from 'lucide-react'
import api from '@/lib/api'
import { apiErrorMessage } from '@/lib/apiError'
import { PageHeader } from '@/components/ui/PageHeader'
import { DataTable } from '@/components/ui/DataTable'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { SelectField, TextAreaField, FormGrid, Tabs, ErrorNote, Badge } from '@/components/ui/FormFields'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { usePermissionsStore } from '@/stores/permissionsStore'
import { StatusBadge } from './RentalsPage'

type Row = Record<string, unknown>
const FREQS = ['monthly', 'quarterly', 'four_months', 'semiannual', 'annual']
const today = () => new Date().toISOString().slice(0, 10)

const emptyOwner = { full_name: '', mobile: '', email: '', national_id: '', address: '', bank_name: '', bank_account: '', iban: '',
  settlement_frequency: 'monthly', commission_rate: '0', settlement_day: '5', notes: '' }

export function OwnersPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { formatEGP } = useFormatNumber()
  const { can, sees } = usePermissionsStore()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') ?? 'owners'
  const [ownerModal, setOwnerModal] = useState<{ open: boolean; row: Row | null }>({ open: false, row: null })
  const [ownerForm, setOwnerForm] = useState<Record<string, string>>(emptyOwner)
  const [settleOpen, setSettleOpen] = useState(false)
  const [settleForm, setSettleForm] = useState({ owner_id: '', period_start: '', period_end: '', adjustments: '0', adjustments_note: '' })
  const [preview, setPreview] = useState<Row | null>(null)
  const [payRow, setPayRow] = useState<Row | null>(null)
  const [payForm, setPayForm] = useState({ amount: '', paid_on: today(), method: 'bank_transfer', reference: '' })
  const [statement, setStatement] = useState<Row | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const owners = useQuery({ queryKey: ['owners'], queryFn: async () => (await api.get<Row[]>('/owners')).data })
  const settlements = useQuery({ queryKey: ['owner-settlements'], queryFn: async () => (await api.get<Row[]>('/owners/settlements')).data })
  const upcoming = useQuery({ queryKey: ['owner-upcoming'], queryFn: async () => (await api.get<Row[]>('/owners/settlements/upcoming')).data })
  const refresh = () => ['owners', 'owner-settlements', 'owner-upcoming', 're-dashboard'].forEach((k) => qc.invalidateQueries({ queryKey: [k] }))
  const financial = sees('owner_financials') || sees('bank_accounts')

  const openOwner = (row: Row | null) => {
    setError(null)
    setOwnerForm(row ? Object.fromEntries(Object.keys(emptyOwner).map((k) => [k, row[k] == null ? '' : String(row[k])])) : emptyOwner)
    setOwnerModal({ open: true, row })
  }

  const saveOwner = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setError(null)
    const payload: Row = { ...ownerForm, commission_rate: Number(ownerForm.commission_rate || 0), settlement_day: Number(ownerForm.settlement_day || 0) }
    for (const k of Object.keys(payload)) if (payload[k] === '') payload[k] = null
    // never send masked values back
    for (const k of ['national_id', 'bank_account', 'iban']) if (String(payload[k] ?? '').startsWith('••••')) delete payload[k]
    if (!financial) { delete payload.bank_name; delete payload.bank_account; delete payload.iban }
    if (!sees('commissions')) delete payload.commission_rate
    try {
      if (ownerModal.row) await api.put(`/owners/${ownerModal.row.id}`, payload)
      else await api.post('/owners', payload)
      setOwnerModal({ open: false, row: null }); refresh()
    } catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }

  const startSettlement = (prefill?: Row) => {
    setError(null); setPreview(null)
    setSettleForm({ owner_id: prefill ? String(prefill.owner_id) : '', period_start: prefill ? String(prefill.period_start) : '',
      period_end: prefill ? String(prefill.period_end) : '', adjustments: '0', adjustments_note: '' })
    setSettleOpen(true)
  }
  const settlementPayload = () => ({ owner_id: Number(settleForm.owner_id), period_start: settleForm.period_start, period_end: settleForm.period_end,
    adjustments: Number(settleForm.adjustments || 0), adjustments_note: settleForm.adjustments_note || null })
  const doPreview = async () => {
    setError(null)
    try { setPreview((await api.post('/owners/settlements/preview', settlementPayload())).data) } catch (err) { setError(apiErrorMessage(err, t)) }
  }
  const createSettlement = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError(null)
    try { await api.post('/owners/settlements', settlementPayload()); setSettleOpen(false); refresh() }
    catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }
  const act = async (row: Row, kind: 'approve' | 'cancel') => {
    try { await api.post(`/owners/settlements/${row.id}/${kind}`); refresh() } catch (err) { alert(apiErrorMessage(err, t)) }
  }
  const pay = async (e: React.FormEvent) => {
    e.preventDefault(); if (!payRow) return
    setBusy(true); setError(null)
    try {
      await api.post(`/owners/settlements/${payRow.id}/payments`, { ...payForm, amount: Number(payForm.amount), reference: payForm.reference || null })
      setPayRow(null); refresh()
    } catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }
  const openStatement = async (row: Row) => {
    try { setStatement((await api.get(`/owners/settlements/${row.id}/statement`)).data) } catch (err) { alert(apiErrorMessage(err, t)) }
  }

  const setTab = (key: string) => setParams((p) => { p.set('tab', key); return p })

  return (
    <div>
      <PageHeader title={t('re.nav.owners')} subtitle={t('re.owners.subtitle')} icon={Landmark} accentIndex={5}
        actions={<>
          {can('owners', 'create') && tab === 'owners' && <Button onClick={() => openOwner(null)}><Plus className="me-2 h-4 w-4" />{t('re.owners.new_owner')}</Button>}
          {can('owners', 'create') && tab !== 'owners' && <Button onClick={() => startSettlement()}><Calculator className="me-2 h-4 w-4" />{t('re.owners.new_settlement')}</Button>}
        </>}
      />
      <Tabs active={tab} onChange={setTab} tabs={[
        { key: 'owners', label: t('re.owners.tab_owners') },
        { key: 'settlements', label: t('re.owners.tab_settlements') },
        { key: 'upcoming', label: t('re.owners.tab_upcoming') },
      ]} />

      {tab === 'owners' && (
        <DataTable title={t('re.owners.tab_owners')} loading={owners.isLoading} data={owners.data ?? []} exportFilename={can('owners', 'export') ? 'owners' : undefined}
          onEmptyAction={can('owners', 'create') ? () => openOwner(null) : undefined}
          columns={[
            { key: 'code', label: t('re.fields.code') },
            { key: 'full_name', label: t('re.fields.owner') },
            { key: 'mobile', label: t('re.fields.mobile') },
            { key: 'units', label: t('re.fields.units_count') },
            { key: 'settlement_frequency', label: t('re.fields.settlement_frequency'), render: (r) => t(`re.freq.${r.settlement_frequency}`) },
            ...(sees('commissions') ? [{ key: 'commission_rate', label: t('re.fields.commission_rate'), render: (r: Row) => `${r.commission_rate}%` }] : []),
            ...(financial ? [{ key: 'bank_account', label: t('re.fields.bank_account'), render: (r: Row) => String(r.bank_account ?? '—') }] : []),
          ]}
          rowActions={can('owners', 'edit') ? (row) => (
            <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openOwner(row)}>{t('edit')}</Button>
          ) : undefined}
        />
      )}

      {tab === 'settlements' && (
        <DataTable title={t('re.owners.tab_settlements')} loading={settlements.isLoading} data={settlements.data ?? []} exportFilename={can('owners', 'export') ? 'owner-settlements' : undefined}
          columns={[
            { key: 'owner_name', label: t('re.fields.owner') },
            { key: 'period_end', label: t('re.fields.period'), render: (r) => `${r.period_start} → ${r.period_end}` },
            { key: 'gross_collected', label: t('re.fields.gross_collected'), render: (r) => formatEGP(r.gross_collected as number) },
            { key: 'commission_amount', label: t('re.fields.commission'), render: (r) => formatEGP(r.commission_amount as number) },
            { key: 'expenses_total', label: t('re.fields.expenses'), render: (r) => formatEGP(r.expenses_total as number) },
            { key: 'net_payable', label: t('re.fields.net_payable'), render: (r) => formatEGP(r.net_payable as number) },
            { key: 'remaining', label: t('re.fields.remaining'), render: (r) => formatEGP(r.remaining as number) },
            { key: 'status', label: t('status'), render: (r) => <StatusBadge value={r.status} /> },
          ]}
          rowActions={(row) => (
            <div className="flex flex-wrap gap-1">
              {row.status === 'draft' && can('owners', 'approve') && <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => act(row, 'approve')}><CheckCircle2 className="me-1 h-3.5 w-3.5" />{t('re.approve')}</Button>}
              {row.status === 'draft' && can('owners', 'cancel') && <Button variant="secondary" className="!px-2 !py-1.5 text-xs text-red-600" onClick={() => act(row, 'cancel')}><XCircle className="me-1 h-3.5 w-3.5" />{t('cancel')}</Button>}
              {['approved', 'partial'].includes(String(row.status)) && can('owners', 'collect') && (row.remaining as number) > 0 && (
                <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => { setError(null); setPayForm({ amount: String(row.remaining), paid_on: today(), method: 'bank_transfer', reference: '' }); setPayRow(row) }}><Wallet className="me-1 h-3.5 w-3.5" />{t('re.owners.pay_owner')}</Button>
              )}
              {can('owners', 'print') && <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => openStatement(row)}><Printer className="me-1 h-3.5 w-3.5" />{t('re.owners.statement')}</Button>}
            </div>
          )}
        />
      )}

      {tab === 'upcoming' && (
        <DataTable title={t('re.owners.tab_upcoming')} loading={upcoming.isLoading} data={upcoming.data ?? []}
          columns={[
            { key: 'owner_name', label: t('re.fields.owner') },
            { key: 'frequency', label: t('re.fields.settlement_frequency'), render: (r) => t(`re.freq.${r.frequency}`) },
            { key: 'period_end', label: t('re.fields.period'), render: (r) => `${r.period_start} → ${r.period_end}` },
            { key: 'due_date', label: t('re.fields.due_date') },
            { key: 'days_until_due', label: t('re.fields.days_until_due'), render: (r) => <Badge tone={(r.days_until_due as number) <= 7 ? 'amber' : 'slate'}>{String(r.days_until_due)}</Badge> },
            { key: 'created', label: t('status'), render: (r) => (r.created ? <Badge tone="green">{t('re.owners.created')}</Badge> : <Badge tone="blue">{t('re.owners.not_created')}</Badge>) },
          ]}
          rowActions={(row) => (!row.created && can('owners', 'create') ? (
            <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => startSettlement(row)}><Calculator className="me-1 h-3.5 w-3.5" />{t('re.owners.prepare')}</Button>
          ) : null)}
        />
      )}

      <Modal open={ownerModal.open} onClose={() => setOwnerModal({ open: false, row: null })} title={ownerModal.row ? t('re.owners.edit_owner') : t('re.owners.new_owner')} className="max-w-2xl">
        <form onSubmit={saveOwner} className="space-y-4">
          <ErrorNote message={error} />
          <FormGrid>
            <Input label={t('re.fields.owner')} value={ownerForm.full_name} onChange={(e) => setOwnerForm({ ...ownerForm, full_name: e.target.value })} required />
            <Input label={t('re.fields.mobile')} value={ownerForm.mobile} onChange={(e) => setOwnerForm({ ...ownerForm, mobile: e.target.value })} dir="ltr" />
            <Input type="email" label={t('email')} value={ownerForm.email} onChange={(e) => setOwnerForm({ ...ownerForm, email: e.target.value })} dir="ltr" />
            <Input label={t('re.fields.national_id')} value={ownerForm.national_id} onChange={(e) => setOwnerForm({ ...ownerForm, national_id: e.target.value })} dir="ltr" />
            <SelectField label={t('re.fields.settlement_frequency')} value={ownerForm.settlement_frequency} onChange={(v) => setOwnerForm({ ...ownerForm, settlement_frequency: v })} required
              options={FREQS.map((f) => ({ value: f, label: t(`re.freq.${f}`) }))} />
            <Input type="number" min="0" max="60" label={t('re.fields.settlement_day')} value={ownerForm.settlement_day} onChange={(e) => setOwnerForm({ ...ownerForm, settlement_day: e.target.value })} />
            {sees('commissions') && <Input type="number" min="0" max="100" step="0.01" label={t('re.fields.commission_rate')} value={ownerForm.commission_rate} onChange={(e) => setOwnerForm({ ...ownerForm, commission_rate: e.target.value })} />}
            {financial && <>
              <Input label={t('re.fields.bank_name')} value={ownerForm.bank_name} onChange={(e) => setOwnerForm({ ...ownerForm, bank_name: e.target.value })} />
              <Input label={t('re.fields.bank_account')} value={ownerForm.bank_account} onChange={(e) => setOwnerForm({ ...ownerForm, bank_account: e.target.value })} dir="ltr" />
              <Input label="IBAN" value={ownerForm.iban} onChange={(e) => setOwnerForm({ ...ownerForm, iban: e.target.value })} dir="ltr" />
            </>}
          </FormGrid>
          <TextAreaField label={t('re.fields.address')} value={ownerForm.address} onChange={(v) => setOwnerForm({ ...ownerForm, address: v })} rows={2} />
          <div className="flex gap-3"><Button type="submit" loading={busy}>{t('save')}</Button><Button type="button" variant="secondary" onClick={() => setOwnerModal({ open: false, row: null })}>{t('cancel')}</Button></div>
        </form>
      </Modal>

      <Modal open={settleOpen} onClose={() => setSettleOpen(false)} title={t('re.owners.new_settlement')} className="max-w-2xl">
        <form onSubmit={createSettlement} className="space-y-4">
          <ErrorNote message={error} />
          <FormGrid>
            <SelectField label={t('re.fields.owner')} value={settleForm.owner_id} onChange={(v) => { setSettleForm({ ...settleForm, owner_id: v }); setPreview(null) }} required
              options={(owners.data ?? []).map((o) => ({ value: String(o.id), label: String(o.full_name) }))} />
            <div />
            <Input type="date" label={t('re.fields.period_start')} value={settleForm.period_start} onChange={(e) => { setSettleForm({ ...settleForm, period_start: e.target.value }); setPreview(null) }} required />
            <Input type="date" label={t('re.fields.period_end')} value={settleForm.period_end} onChange={(e) => { setSettleForm({ ...settleForm, period_end: e.target.value }); setPreview(null) }} required />
            {can('owners', 'approve') && <>
              <Input type="number" step="0.01" label={t('re.fields.adjustments')} value={settleForm.adjustments} onChange={(e) => { setSettleForm({ ...settleForm, adjustments: e.target.value }); setPreview(null) }} />
              <Input label={t('re.fields.adjustments_note')} value={settleForm.adjustments_note} onChange={(e) => setSettleForm({ ...settleForm, adjustments_note: e.target.value })} />
            </>}
          </FormGrid>
          <Button type="button" variant="secondary" onClick={doPreview} disabled={!settleForm.owner_id || !settleForm.period_end}><Calculator className="me-2 h-4 w-4" />{t('re.owners.calculate')}</Button>
          {preview && (
            <div className="rounded-xl border border-primary-100 bg-primary-50/50 p-4 text-sm">
              <dl className="grid gap-2 sm:grid-cols-2">
                <dt className="text-slate-600">{t('re.fields.gross_collected')}</dt><dd className="font-semibold">{formatEGP(preview.gross_collected as number)}</dd>
                <dt className="text-slate-600">− {t('re.fields.commission')}</dt><dd className="font-semibold">{formatEGP(preview.commission_amount as number)}</dd>
                <dt className="text-slate-600">− {t('re.fields.expenses')}</dt><dd className="font-semibold">{formatEGP(preview.expenses_total as number)}</dd>
                <dt className="text-slate-600">± {t('re.fields.adjustments')}</dt><dd className="font-semibold">{formatEGP(preview.adjustments as number)}</dd>
                <dt className="border-t border-primary-100 pt-2 font-semibold text-slate-900">{t('re.fields.net_payable')}</dt>
                <dd className="border-t border-primary-100 pt-2 text-lg font-bold text-primary-800">{formatEGP(preview.net_payable as number)}</dd>
              </dl>
              <p className="mt-3 text-xs text-slate-500">{t('re.owners.calc_note')}</p>
            </div>
          )}
          <div className="flex gap-3"><Button type="submit" loading={busy} disabled={!preview}>{t('re.owners.create_draft')}</Button><Button type="button" variant="secondary" onClick={() => setSettleOpen(false)}>{t('cancel')}</Button></div>
        </form>
      </Modal>

      <Modal open={!!payRow} onClose={() => setPayRow(null)} title={t('re.owners.pay_owner')}>
        <form onSubmit={pay} className="space-y-4">
          <ErrorNote message={error} />
          <p className="text-sm text-slate-600">{String(payRow?.owner_name ?? '')} — {t('re.fields.remaining')}: {formatEGP(payRow?.remaining as number)}</p>
          <Input type="number" min="0.01" step="0.01" label={t('re.fields.amount')} value={payForm.amount} onChange={(e) => setPayForm({ ...payForm, amount: e.target.value })} required />
          <Input type="date" label={t('re.fields.date')} value={payForm.paid_on} onChange={(e) => setPayForm({ ...payForm, paid_on: e.target.value })} required />
          <SelectField label={t('re.fields.method')} value={payForm.method} onChange={(v) => setPayForm({ ...payForm, method: v })} options={['bank_transfer', 'cash', 'cheque', 'instapay'].map((m) => ({ value: m, label: t(`re.method.${m}`) }))} />
          <Input label={t('re.fields.receipt_reference')} value={payForm.reference} onChange={(e) => setPayForm({ ...payForm, reference: e.target.value })} />
          <div className="flex gap-3"><Button type="submit" loading={busy}>{t('re.confirm')}</Button><Button type="button" variant="secondary" onClick={() => setPayRow(null)}>{t('cancel')}</Button></div>
        </form>
      </Modal>

      <Modal open={!!statement} onClose={() => setStatement(null)} title={t('re.owners.statement')} className="max-w-2xl">
        {statement && (() => {
          const s = statement.settlement as Row
          const calc = (s.calculation ?? { contracts: [], expenses: [] }) as { contracts: Row[]; expenses: Row[] }
          return (
            <div className="space-y-4 text-sm print:text-xs">
              <div className="flex flex-wrap justify-between gap-2">
                <div><p className="font-semibold">{String(s.owner_name)}</p><p className="text-slate-500">{String(s.period_start)} → {String(s.period_end)}</p></div>
                <StatusBadge value={s.status} />
              </div>
              <table className="w-full"><tbody>
                {calc.contracts.map((c) => <tr key={String(c.contract_id)} className="border-b border-slate-100"><td className="py-1">{String(c.contract_number)}</td><td className="py-1 text-end">{formatEGP(c.collected as number)}</td><td className="py-1 text-end text-slate-500">−{formatEGP(c.commission as number)}</td></tr>)}
                {calc.expenses.map((e) => <tr key={`e${String(e.id)}`} className="border-b border-slate-100"><td className="py-1">{t('re.fields.expenses')}: {String(e.category)} ({String(e.date)})</td><td /><td className="py-1 text-end text-slate-500">−{formatEGP(e.amount as number)}</td></tr>)}
              </tbody></table>
              <dl className="grid grid-cols-2 gap-1">
                <dt>{t('re.fields.gross_collected')}</dt><dd className="text-end">{formatEGP(s.gross_collected as number)}</dd>
                <dt>{t('re.fields.commission')}</dt><dd className="text-end">{formatEGP(s.commission_amount as number)}</dd>
                <dt>{t('re.fields.expenses')}</dt><dd className="text-end">{formatEGP(s.expenses_total as number)}</dd>
                <dt>{t('re.fields.adjustments')}</dt><dd className="text-end">{formatEGP(s.adjustments as number)}</dd>
                <dt className="font-semibold">{t('re.fields.net_payable')}</dt><dd className="text-end font-semibold">{formatEGP(s.net_payable as number)}</dd>
                <dt>{t('re.fields.paid')}</dt><dd className="text-end">{formatEGP(s.amount_paid as number)}</dd>
                <dt>{t('re.fields.remaining')}</dt><dd className="text-end">{formatEGP(s.remaining as number)}</dd>
              </dl>
              <Button variant="secondary" onClick={() => window.print()} className="print:hidden"><Printer className="me-2 h-4 w-4" />{t('re.print')}</Button>
            </div>
          )
        })()}
      </Modal>
    </div>
  )
}
