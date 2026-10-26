import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Presentation, Plus, RotateCcw, Ban, PlayCircle, Settings2, History, Copy, Link2, RefreshCw } from 'lucide-react'
import api from '@/lib/api'
import { apiErrorMessage } from '@/lib/apiError'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { SelectField, FormGrid, ErrorNote, Badge, TextAreaField } from '@/components/ui/FormFields'

type Named = { key: string; name_ar: string; name_en: string }
type Options = { profiles: (Named & { modules: string[]; cards: string[] })[]; modules: Named[]; actions: Named[]; default_actions: string[]; cards: (Named & { module: string })[]; roles: string[] }
type Demo = { id: number; company_id: number; company_code: string; company_name_ar: string; company_name_en: string; prospect_name: string; profile: string
  enabled_modules: string[]; allowed_actions: string[]; dashboard_cards: string[] | null; expires_at: string | null; is_enabled: boolean
  revoked_at: string | null; last_reset_at: string | null; status: string; notes: string | null
  link_path: string | null; days_left: number | null
  users: { id: number; username: string; system_role: string; status: string }[] }

const STATUS_TONE: Record<string, 'green' | 'red' | 'amber' | 'slate'> = { active: 'green', demo_expired: 'amber', demo_revoked: 'red', demo_disabled: 'slate' }

const linkUrl = (path: string) => `${window.location.origin}${path}`

export function DemosPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const label = (x: Named) => (i18n.language === 'ar' ? x.name_ar : x.name_en)
  const options = useQuery({ queryKey: ['demo-options'], queryFn: async () => (await api.get<Options>('/demos/options')).data })
  const demos = useQuery({ queryKey: ['demos'], queryFn: async () => (await api.get<Demo[]>('/demos')).data })
  const [editing, setEditing] = useState<Partial<Demo> & { mode: 'create' | 'edit'; role?: string; valid_days?: string } | null>(null)
  const [newLink, setNewLink] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [auditFor, setAuditFor] = useState<Demo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const audit = useQuery({
    queryKey: ['demo-audit', auditFor?.id], enabled: !!auditFor,
    queryFn: async () => (await api.get<{ id: number; action: string; user: string | null; created_at: string; details: string | null }[]>(`/demos/${auditFor?.id}/audit`)).data,
  })
  const refresh = () => qc.invalidateQueries({ queryKey: ['demos'] })

  const startCreate = () => {
    const profile = options.data?.profiles.find((p) => p.key === 'full_erp')
    setError(null)
    setEditing({ mode: 'create', profile: 'full_erp', prospect_name: '', company_name_ar: '', company_name_en: '', enabled_modules: profile?.modules ?? [],
      allowed_actions: options.data?.default_actions ?? [], dashboard_cards: profile?.cards ?? [], valid_days: '14', notes: '', role: 'company_admin' })
  }
  const pickProfile = (key: string) => {
    const p = options.data?.profiles.find((x) => x.key === key)
    if (!p || !editing) return
    setEditing({ ...editing, profile: key, enabled_modules: p.modules, dashboard_cards: p.cards })
  }
  const toggleIn = (field: 'enabled_modules' | 'allowed_actions' | 'dashboard_cards', key: string) => {
    if (!editing) return
    const list = (editing[field] as string[] | null) ?? []
    setEditing({ ...editing, [field]: list.includes(key) ? list.filter((x) => x !== key) : [...list, key] })
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editing) return
    setBusy(true); setError(null)
    const body = {
      prospect_name: editing.prospect_name, company_name_ar: editing.company_name_ar, company_name_en: editing.company_name_en,
      profile: editing.profile, enabled_modules: editing.enabled_modules, allowed_actions: editing.allowed_actions,
      dashboard_cards: editing.dashboard_cards, notes: editing.notes || null,
      ...(editing.valid_days ? { valid_days: Number(editing.valid_days) } : {}),
    }
    try {
      if (editing.mode === 'create') {
        const { data } = await api.post<Demo>('/demos', { ...body, users: [{ role: editing.role || 'company_admin' }] })
        if (data.link_path) setNewLink(linkUrl(data.link_path))
      } else {
        await api.put(`/demos/${editing.id}`, body)
      }
      setEditing(null); refresh()
    } catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }

  const act = async (demo: Demo, path: string, confirmKey?: string) => {
    if (confirmKey && !window.confirm(t(confirmKey))) return
    try { await api.post(`/demos/${demo.id}/${path}`); refresh() } catch (err) { alert(apiErrorMessage(err, t)) }
  }
  const copy = async (url: string) => {
    try { await navigator.clipboard?.writeText(url) } catch { /* clipboard unavailable */ }
    setCopied(url)
    window.setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div>
      <PageHeader title={t('re.nav.demos')} subtitle={t('re.demos.subtitle')} icon={Presentation} accentIndex={1}
        actions={<Button onClick={startCreate} disabled={!options.data}><Plus className="me-2 h-4 w-4" />{t('re.demos.new')}</Button>} />

      <div className="grid gap-4 lg:grid-cols-2">
        {(demos.data ?? []).map((d) => (
          <Card key={d.id}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-semibold text-slate-900">{d.prospect_name}</p>
                <p className="text-sm text-slate-500">{i18n.language === 'ar' ? d.company_name_ar : d.company_name_en} · {d.company_code}</p>
              </div>
              <Badge tone={STATUS_TONE[d.status] ?? 'slate'}>{t(`re.demos.status.${d.status}`)}</Badge>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
              <dt>{t('re.demos.profile')}</dt><dd>{label(options.data?.profiles.find((p) => p.key === d.profile) ?? { key: d.profile, name_ar: d.profile, name_en: d.profile })}</dd>
              <dt>{t('re.demos.expires')}</dt><dd>{d.expires_at ? new Date(d.expires_at).toLocaleString(i18n.language === 'ar' ? 'ar-EG' : 'en-GB') : '—'}</dd>
              <dt>{t('re.demos.last_reset')}</dt><dd>{d.last_reset_at ? new Date(d.last_reset_at).toLocaleString(i18n.language === 'ar' ? 'ar-EG' : 'en-GB') : '—'}</dd>
              <dt>{t('re.demos.modules')}</dt><dd>{d.enabled_modules.length}</dd>
              <dt>{t('re.demos.days_left')}</dt><dd>{d.days_left ?? '—'}</dd>
            </dl>
            {d.link_path && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 p-2">
                <Link2 className="h-4 w-4 shrink-0 text-violet-700" />
                <code className="min-w-0 flex-1 truncate text-xs text-violet-900" dir="ltr">{linkUrl(d.link_path)}</code>
                <Button variant="secondary" className="!px-2 !py-1 text-xs" onClick={() => copy(linkUrl(d.link_path!))}>
                  <Copy className="me-1 h-3 w-3" />{copied === linkUrl(d.link_path) ? t('re.copied') : t('re.copy')}
                </Button>
              </div>
            )}
            <div className="mt-4 flex flex-wrap gap-1.5">
              <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => { setError(null); setEditing({ ...d, mode: 'edit', valid_days: '' }) }}><Settings2 className="me-1 h-3.5 w-3.5" />{t('re.demos.configure')}</Button>
              <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => act(d, 'reset', 're.demos.confirm_reset')}><RotateCcw className="me-1 h-3.5 w-3.5" />{t('re.demos.reset')}</Button>
              {d.status === 'demo_revoked' || !d.is_enabled
                ? <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => act(d, 'restore')}><PlayCircle className="me-1 h-3.5 w-3.5" />{t('re.demos.restore')}</Button>
                : <Button variant="secondary" className="!px-2 !py-1.5 text-xs text-red-600" onClick={() => act(d, 'revoke', 're.demos.confirm_revoke')}><Ban className="me-1 h-3.5 w-3.5" />{t('re.demos.revoke')}</Button>}
              <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => act(d, 'link', 're.demos.confirm_new_link')}><RefreshCw className="me-1 h-3.5 w-3.5" />{t('re.demos.new_link')}</Button>
              <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => setAuditFor(d)}><History className="me-1 h-3.5 w-3.5" />{t('re.demos.audit')}</Button>
            </div>
          </Card>
        ))}
        {!demos.isLoading && !(demos.data ?? []).length && <Card className="lg:col-span-2"><p className="text-center text-slate-500">{t('re.demos.none')}</p></Card>}
      </div>

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.mode === 'create' ? t('re.demos.new') : t('re.demos.configure')} className="max-w-4xl">
        {editing && options.data && (
          <form onSubmit={submit} className="space-y-5">
            <ErrorNote message={error} />
            <FormGrid>
              <Input label={t('re.demos.prospect')} value={editing.prospect_name ?? ''} onChange={(e) => setEditing({ ...editing, prospect_name: e.target.value })} required />
              <SelectField label={t('re.demos.profile')} value={editing.profile ?? ''} onChange={pickProfile} required options={options.data.profiles.map((p) => ({ value: p.key, label: label(p) }))} />
              <Input label={t('re.demos.company_ar')} value={editing.company_name_ar ?? ''} onChange={(e) => setEditing({ ...editing, company_name_ar: e.target.value })} required />
              <Input label={t('re.demos.company_en')} value={editing.company_name_en ?? ''} onChange={(e) => setEditing({ ...editing, company_name_en: e.target.value })} required dir="ltr" />
              <Input type="number" min="1" max="365" label={editing.mode === 'create' ? t('re.demos.valid_days') : t('re.demos.extend_days')}
                value={editing.valid_days ?? ''} onChange={(e) => setEditing({ ...editing, valid_days: e.target.value })} required={editing.mode === 'create'}
                placeholder={editing.mode === 'edit' && editing.expires_at ? new Date(editing.expires_at).toLocaleDateString(i18n.language === 'ar' ? 'ar-EG' : 'en-GB') : '14'} />
              {editing.mode === 'create' && (
                <SelectField label={t('re.demos.first_user_role')} value={editing.role ?? 'company_admin'} onChange={(v) => setEditing({ ...editing, role: v })}
                  options={options.data.roles.map((r) => ({ value: r, label: t(`re.system_role.${r}`, { defaultValue: r }) }))} />
              )}
            </FormGrid>
            <fieldset>
              <legend className="mb-2 text-sm font-semibold text-slate-800">{t('re.demos.modules')}</legend>
              <div className="flex flex-wrap gap-2">{options.data.modules.map((m) => (
                <label key={m.key} className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs">
                  <input type="checkbox" checked={(editing.enabled_modules ?? []).includes(m.key)} disabled={m.key === 'dashboard'} onChange={() => toggleIn('enabled_modules', m.key)} />{label(m)}
                </label>))}</div>
            </fieldset>
            <fieldset>
              <legend className="mb-2 text-sm font-semibold text-slate-800">{t('re.demos.actions')}</legend>
              <div className="flex flex-wrap gap-2">{options.data.actions.map((a) => (
                <label key={a.key} className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs">
                  <input type="checkbox" checked={(editing.allowed_actions ?? []).includes(a.key)} disabled={a.key === 'view'} onChange={() => toggleIn('allowed_actions', a.key)} />{label(a)}
                </label>))}</div>
              <p className="mt-1 text-xs text-slate-500">{t('re.demos.actions_help')}</p>
            </fieldset>
            <fieldset>
              <legend className="mb-2 text-sm font-semibold text-slate-800">{t('re.demos.cards')}</legend>
              <div className="flex flex-wrap gap-2">{options.data.cards.map((c) => (
                <label key={c.key} className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs">
                  <input type="checkbox" checked={(editing.dashboard_cards ?? []).includes(c.key)} onChange={() => toggleIn('dashboard_cards', c.key)} />{label(c)}
                </label>))}</div>
            </fieldset>
            <TextAreaField label={t('re.fields.notes')} value={editing.notes ?? ''} onChange={(v) => setEditing({ ...editing, notes: v })} rows={2} />
            <div className="flex gap-3"><Button type="submit" loading={busy}>{editing.mode === 'create' ? t('re.demos.create_and_seed') : t('save')}</Button><Button type="button" variant="secondary" onClick={() => setEditing(null)}>{t('cancel')}</Button></div>
          </form>
        )}
      </Modal>

      <Modal open={!!newLink} onClose={() => setNewLink(null)} title={t('re.demos.link_ready')}>
        <div className="space-y-3">
          <p className="text-sm text-slate-600">{t('re.demos.link_help')}</p>
          <div className="rounded-lg border border-violet-200 bg-violet-50 p-3 font-mono text-sm break-all" dir="ltr">{newLink}</div>
          <Button onClick={() => newLink && copy(newLink)}><Copy className="me-2 h-4 w-4" />{copied === newLink ? t('re.copied') : t('re.copy')}</Button>
        </div>
      </Modal>

      <Modal open={!!auditFor} onClose={() => setAuditFor(null)} title={t('re.demos.audit')} className="max-w-2xl">
        <ul className="max-h-[60vh] divide-y divide-slate-100 overflow-y-auto text-sm">
          {(audit.data ?? []).map((a) => (
            <li key={a.id} className="flex flex-wrap justify-between gap-2 py-2">
              <span>{t(`re.audit.${a.action}`, { defaultValue: a.action })}{a.details ? <span className="text-xs text-slate-500"> — {a.details}</span> : null}</span>
              <span className="text-xs text-slate-500">{a.user ?? '—'} · {new Date(a.created_at).toLocaleString(i18n.language === 'ar' ? 'ar-EG' : 'en-GB')}</span>
            </li>
          ))}
        </ul>
      </Modal>
    </div>
  )
}
