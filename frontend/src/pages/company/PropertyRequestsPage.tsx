import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, Sparkles, CheckCircle2, XCircle, HelpCircle } from 'lucide-react'
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

type Row = Record<string, unknown>
type Match = { source: string; id: number; title: string; contact_name: string | null; contact_mobile: string | null; score: number
  matched: { key: string; name_ar: string; name_en: string }[]; mismatched: { key: string; name_ar: string; name_en: string }[]
  unknown: { key: string; name_ar: string; name_en: string }[] }

const KINDS = ['offer_sale', 'offer_rent', 'request_buy', 'request_rent']
const TYPES = ['apartment', 'villa', 'duplex', 'penthouse', 'chalet', 'office', 'retail', 'clinic', 'warehouse', 'land']
const empty = { kind: 'request_rent', customer_name: '', customer_mobile: '', property_type: 'apartment', city: '', district: '', price_min: '', price_max: '',
  area_min: '', area_max: '', rooms: '', floor: '', construction_year: '', finishing: '', furnishing_status: '', has_utility_meters: '', meter_notes: '', notes: '' }

export function PropertyRequestsPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const { formatEGP } = useFormatNumber()
  const can = usePermissionsStore((s) => s.can)
  const [params, setParams] = useSearchParams()
  const kind = params.get('kind') ?? 'all'
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<Record<string, string>>(empty)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [matchFor, setMatchFor] = useState<Row | null>(null)
  const [criteria, setCriteria] = useState<string[]>([])

  const list = useQuery({
    queryKey: ['property-requests', kind],
    queryFn: async () => (await api.get<Row[]>(`/re-requests${kind !== 'all' ? `?kind=${kind}` : ''}`)).data,
  })
  const criteriaCatalog = useQuery({ queryKey: ['match-criteria'], queryFn: async () => (await api.get<{ key: string; name_ar: string; name_en: string; required: boolean }[]>('/re-requests/criteria')).data })
  const matches = useQuery({
    queryKey: ['matches', matchFor?.id, criteria.join(',')], enabled: !!matchFor,
    queryFn: async () => (await api.get<Match[]>(`/re-requests/${matchFor?.id}/matches${criteria.length ? `?criteria=${criteria.join(',')}` : ''}`)).data,
  })
  const label = (x: { name_ar: string; name_en: string }) => (i18n.language === 'ar' ? x.name_ar : x.name_en)

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError(null)
    const payload: Row = { ...form }
    for (const k of ['price_min', 'price_max', 'area_min', 'area_max', 'rooms', 'floor', 'construction_year']) payload[k] = form[k] === '' ? null : Number(form[k])
    for (const k of ['city', 'district', 'finishing', 'furnishing_status', 'meter_notes', 'notes']) if (payload[k] === '') payload[k] = null
    payload.has_utility_meters = form.has_utility_meters === '' ? null : form.has_utility_meters === 'yes'
    try { await api.post('/re-requests', payload); setOpen(false); setForm(empty); qc.invalidateQueries({ queryKey: ['property-requests'] }) }
    catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }

  const range = (lo: unknown, hi: unknown, fmt: (v: number) => string) =>
    lo == null && hi == null ? '—' : `${lo != null ? fmt(lo as number) : '…'} – ${hi != null ? fmt(hi as number) : '…'}`

  return (
    <div>
      <PageHeader title={t('re.nav.requests')} subtitle={t('re.requests.subtitle')} icon={Search} accentIndex={0}
        actions={can('real_estate_requests', 'create') ? <Button onClick={() => { setError(null); setOpen(true) }}><Plus className="me-2 h-4 w-4" />{t('re.requests.new')}</Button> : undefined} />
      <Tabs active={kind} onChange={(k) => setParams((p) => { p.set('kind', k); return p })} tabs={[
        { key: 'all', label: t('re.requests.all') }, { key: 'offer', label: t('re.requests.offers') }, { key: 'request', label: t('re.requests.requests') },
        ...KINDS.map((k) => ({ key: k, label: t(`re.kind.${k}`) })),
      ]} />
      <DataTable title={t('re.nav.requests')} loading={list.isLoading} data={list.data ?? []} exportFilename={can('real_estate_requests', 'export') ? 'property-requests' : undefined}
        columns={[
          { key: 'kind', label: t('re.fields.kind'), render: (r) => <Badge tone={String(r.kind).startsWith('offer') ? 'violet' : 'blue'}>{t(`re.kind.${r.kind}`)}</Badge> },
          { key: 'customer_name', label: t('re.fields.customer') },
          { key: 'customer_mobile', label: t('re.fields.mobile') },
          { key: 'property_type', label: t('re.fields.property_type'), render: (r) => (r.property_type ? t(`re.unit_type.${r.property_type}`, { defaultValue: String(r.property_type) }) : '—') },
          { key: 'city', label: t('re.fields.location'), render: (r) => [r.city, r.district].filter(Boolean).join(' — ') || '—' },
          { key: 'price_max', label: t('re.fields.budget'), render: (r) => range(r.price_min, r.price_max, formatEGP) },
          { key: 'area_max', label: t('re.fields.area'), render: (r) => range(r.area_min, r.area_max, (v) => `${v} ${t('re.sqm')}`) },
          { key: 'status', label: t('status'), render: (r) => <Badge>{t(`re.status.${r.status}`, { defaultValue: String(r.status) })}</Badge> },
        ]}
        rowActions={(row) => (
          <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => { setCriteria([]); setMatchFor(row) }}>
            <Sparkles className="me-1 h-3.5 w-3.5" />{t('re.requests.find_matches')}
          </Button>
        )}
      />

      <Modal open={open} onClose={() => setOpen(false)} title={t('re.requests.new')} className="max-w-3xl">
        <form onSubmit={save} className="space-y-4">
          <ErrorNote message={error} />
          <FormGrid>
            <SelectField label={t('re.fields.kind')} value={form.kind} onChange={(v) => setForm({ ...form, kind: v })} required options={KINDS.map((k) => ({ value: k, label: t(`re.kind.${k}`) }))} />
            <SelectField label={t('re.fields.property_type')} value={form.property_type} onChange={(v) => setForm({ ...form, property_type: v })} options={TYPES.map((k) => ({ value: k, label: t(`re.unit_type.${k}`) }))} />
            <Input label={t('re.fields.customer')} value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} required />
            <Input label={t('re.fields.mobile')} value={form.customer_mobile} onChange={(e) => setForm({ ...form, customer_mobile: e.target.value })} required dir="ltr" />
            <Input label={t('re.fields.city')} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            <Input label={t('re.fields.district')} value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
            <Input type="number" min="0" label={t('re.fields.price_min')} value={form.price_min} onChange={(e) => setForm({ ...form, price_min: e.target.value })} />
            <Input type="number" min="0" label={t('re.fields.price_max')} value={form.price_max} onChange={(e) => setForm({ ...form, price_max: e.target.value })} />
            <Input type="number" min="0" label={t('re.fields.area_min')} value={form.area_min} onChange={(e) => setForm({ ...form, area_min: e.target.value })} />
            <Input type="number" min="0" label={t('re.fields.area_max')} value={form.area_max} onChange={(e) => setForm({ ...form, area_max: e.target.value })} />
            <Input type="number" min="0" label={t('re.fields.rooms')} value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} />
            <Input type="number" label={t('re.fields.floor')} value={form.floor} onChange={(e) => setForm({ ...form, floor: e.target.value })} />
            <Input type="number" min="1900" max="2100" label={t('re.fields.construction_year')} value={form.construction_year} onChange={(e) => setForm({ ...form, construction_year: e.target.value })} />
            <SelectField label={t('re.fields.finishing')} value={form.finishing} onChange={(v) => setForm({ ...form, finishing: v })} options={['core_shell', 'semi', 'full', 'super_lux'].map((k) => ({ value: k, label: t(`re.finishing.${k}`) }))} />
            <SelectField label={t('re.fields.furnishing')} value={form.furnishing_status} onChange={(v) => setForm({ ...form, furnishing_status: v })} options={['unfurnished', 'semi', 'furnished'].map((k) => ({ value: k, label: t(`re.furnishing.${k}`) }))} />
            <SelectField label={t('re.fields.meters')} value={form.has_utility_meters} onChange={(v) => setForm({ ...form, has_utility_meters: v })} options={[{ value: 'yes', label: t('re.yes') }, { value: 'no', label: t('re.no') }]} />
          </FormGrid>
          <Input label={t('re.fields.meter_notes')} value={form.meter_notes} onChange={(e) => setForm({ ...form, meter_notes: e.target.value })} />
          <TextAreaField label={t('re.fields.notes')} value={form.notes} onChange={(v) => setForm({ ...form, notes: v })} rows={2} />
          <div className="flex gap-3"><Button type="submit" loading={busy}>{t('save')}</Button><Button type="button" variant="secondary" onClick={() => setOpen(false)}>{t('cancel')}</Button></div>
        </form>
      </Modal>

      <Modal open={!!matchFor} onClose={() => setMatchFor(null)} title={t('re.requests.matches_for', { name: String(matchFor?.customer_name ?? '') })} className="max-w-3xl">
        <div className="space-y-4">
          <div>
            <p className="mb-2 text-sm font-medium text-slate-700">{t('re.requests.criteria')}</p>
            <div className="flex flex-wrap gap-2">
              {(criteriaCatalog.data ?? []).map((c) => {
                const active = criteria.length === 0 || criteria.includes(c.key)
                return (
                  <button key={c.key} type="button" disabled={c.required}
                    className={`rounded-full border px-3 py-1 text-xs ${active ? 'border-primary-500 bg-primary-50 text-primary-800' : 'border-slate-200 text-slate-500'}`}
                    onClick={() => {
                      const base = criteria.length === 0 ? (criteriaCatalog.data ?? []).map((x) => x.key) : criteria
                      setCriteria(base.includes(c.key) ? base.filter((k) => k !== c.key) : [...base, c.key])
                    }}>
                    {label(c)}{c.required ? ' *' : ''}
                  </button>
                )
              })}
            </div>
            <p className="mt-2 text-xs text-slate-500">{t('re.requests.unknown_note')}</p>
          </div>
          {matches.isLoading ? <p className="text-slate-500">{t('loading')}</p> : (matches.data ?? []).length === 0 ? (
            <p className="rounded-lg bg-slate-50 p-6 text-center text-slate-500">{t('re.requests.no_matches')}</p>
          ) : (
            <ul className="space-y-3">
              {(matches.data ?? []).map((m) => (
                <li key={`${m.source}-${m.id}`} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold text-slate-900">{m.title}</p>
                      <p className="text-xs text-slate-500">{t(`re.match_source.${m.source}`)}{m.contact_name ? ` — ${m.contact_name} ${m.contact_mobile ?? ''}` : ''}</p>
                    </div>
                    <Badge tone={m.score >= 0.7 ? 'green' : m.score >= 0.4 ? 'amber' : 'slate'}>{Math.round(m.score * 100)}%</Badge>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
                    {m.matched.map((c) => <span key={c.key} className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-800"><CheckCircle2 className="h-3 w-3" />{label(c)}</span>)}
                    {m.mismatched.map((c) => <span key={c.key} className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-red-700"><XCircle className="h-3 w-3" />{label(c)}</span>)}
                    {m.unknown.map((c) => <span key={c.key} className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-slate-600"><HelpCircle className="h-3 w-3" />{label(c)}</span>)}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Modal>
    </div>
  )
}
