import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { KeyRound, Plus, Copy, Trash2, Save, ShieldCheck, History, UserCog } from 'lucide-react'
import api from '@/lib/api'
import { apiErrorMessage } from '@/lib/apiError'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { SelectField, Tabs, ErrorNote, SuccessNote, Badge } from '@/components/ui/FormFields'
import { usePermissionsStore } from '@/stores/permissionsStore'

type Named = { key: string; name_ar: string; name_en: string }
type Catalog = {
  modules: (Named & { category_ar: string; category_en: string; enabled: boolean; pages: Named[] })[]
  actions: Named[]
  field_groups: Named[]
  data_scopes: Named[]
  templates: Named[]
}
type Role = { id: number; name_ar: string; name_en: string; code: string; description: string | null; data_scope: string
  field_access: string[]; permissions: Record<string, string[]>; is_active: boolean; users_count: number }
type Draft = Omit<Role, 'id' | 'users_count' | 'code'> & { id?: number }

const blank: Draft = { name_ar: '', name_en: '', description: '', data_scope: 'own', field_access: [], permissions: {}, is_active: true }

export function RolesPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const perms = usePermissionsStore()
  const canManage = perms.can('users', 'manage_permissions')
  const [tab, setTab] = useState('roles')
  const [draft, setDraft] = useState<Draft | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [ok, setOk] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [templateOpen, setTemplateOpen] = useState(false)
  const [template, setTemplate] = useState('')
  const [assignUser, setAssignUser] = useState<number | null>(null)
  const label = (x: Named) => (i18n.language === 'ar' ? x.name_ar : x.name_en)

  const catalog = useQuery({ queryKey: ['perm-catalog'], queryFn: async () => (await api.get<Catalog>('/roles/catalog')).data })
  const roles = useQuery({ queryKey: ['roles'], queryFn: async () => (await api.get<Role[]>('/roles')).data })
  const users = useQuery({ queryKey: ['company-users'], queryFn: async () => (await api.get<{ items: { id: number; full_name_ar: string; full_name_en: string; email: string; system_role: string; status: string }[] }>('/users?page_size=100')).data.items })
  const assignment = useQuery({
    queryKey: ['role-assignment', assignUser], enabled: !!assignUser,
    queryFn: async () => (await api.get<{ role_ids: number[]; system_role: string; effective: { permissions: Record<string, string[]>; data_scope: string; field_access: string[] } }>(`/roles/assignments/${assignUser}`)).data,
  })
  const audit = useQuery({ queryKey: ['perm-audit'], enabled: tab === 'audit' && canManage, queryFn: async () => (await api.get<{ id: number; action: string; user: string | null; created_at: string; entity_id: number | null }[]>('/roles/audit/log')).data })
  const [assignIds, setAssignIds] = useState<number[] | null>(null)

  const modules = useMemo(() => (catalog.data?.modules ?? []).filter((m) => m.enabled), [catalog.data])
  const actions = catalog.data?.actions ?? []
  const refresh = () => {
    ['roles', 'role-assignment', 'perm-audit'].forEach((k) => qc.invalidateQueries({ queryKey: [k] }))
    perms.fetch()
  }

  const toggle = (module: string, action: string) => {
    if (!draft) return
    const current = new Set(draft.permissions[module] ?? [])
    if (current.has(action)) current.delete(action)
    else { current.add(action); if (action !== 'view') current.add('view') }
    setDraft({ ...draft, permissions: { ...draft.permissions, [module]: Array.from(current) } })
  }
  const toggleRow = (module: string) => {
    if (!draft) return
    const grantable = actions.map((a) => a.key).filter((a) => perms.can(module, a))
    const all = grantable.every((a) => (draft.permissions[module] ?? []).includes(a))
    setDraft({ ...draft, permissions: { ...draft.permissions, [module]: all ? [] : grantable } })
  }

  const save = async () => {
    if (!draft) return
    setBusy(true); setError(null); setOk(null)
    const payload = { ...draft, permissions: Object.fromEntries(Object.entries(draft.permissions).filter(([, a]) => a.length)) }
    try {
      if (draft.id) await api.put(`/roles/${draft.id}`, payload)
      else await api.post('/roles', payload)
      setOk(t('re.roles.saved')); setDraft(null); refresh()
    } catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }
  const remove = async (role: Role) => {
    if (!window.confirm(t('re.roles.confirm_delete'))) return
    try { await api.delete(`/roles/${role.id}`); refresh() } catch (err) { setError(apiErrorMessage(err, t)) }
  }
  const fromTemplate = async () => {
    setBusy(true); setError(null)
    try { await api.post('/roles/from-template', { template }); setTemplateOpen(false); refresh() }
    catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }
  const saveAssignment = async () => {
    if (!assignUser || !assignIds) return
    setBusy(true); setError(null)
    try { await api.put(`/roles/assignments/${assignUser}`, { role_ids: assignIds }); setOk(t('re.roles.saved')); refresh() }
    catch (err) { setError(apiErrorMessage(err, t)) } finally { setBusy(false) }
  }

  return (
    <div>
      <PageHeader title={t('re.nav.roles')} subtitle={t('re.roles.subtitle')} icon={KeyRound} accentIndex={4}
        actions={canManage && tab === 'roles' ? <>
          <Button variant="secondary" onClick={() => { setError(null); setTemplateOpen(true) }}><Copy className="me-2 h-4 w-4" />{t('re.roles.from_template')}</Button>
          <Button onClick={() => { setError(null); setDraft({ ...blank }) }}><Plus className="me-2 h-4 w-4" />{t('re.roles.new')}</Button>
        </> : undefined} />
      <Tabs active={tab} onChange={setTab} tabs={[
        { key: 'roles', label: t('re.roles.tab_roles') },
        { key: 'assign', label: t('re.roles.tab_assign') },
        ...(canManage ? [{ key: 'audit', label: t('re.roles.tab_audit') }] : []),
      ]} />
      <ErrorNote message={error} />
      <SuccessNote message={ok} />

      {tab === 'roles' && !draft && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(roles.data ?? []).map((r) => (
            <Card key={r.id}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-slate-900">{i18n.language === 'ar' ? r.name_ar : r.name_en}</p>
                  <p className="text-xs text-slate-500">{r.code}</p>
                </div>
                <Badge tone={r.is_active ? 'green' : 'slate'}>{r.is_active ? t('re.active') : t('re.inactive')}</Badge>
              </div>
              <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
                <Badge tone="blue">{t('re.roles.scope')}: {t(`re.scope.${r.data_scope}`)}</Badge>
                <Badge>{t('re.roles.users_count', { count: r.users_count })}</Badge>
                <Badge tone="violet">{Object.keys(r.permissions).length} {t('re.roles.modules')}</Badge>
              </div>
              {canManage && (
                <div className="mt-4 flex gap-2">
                  <Button variant="secondary" className="!px-3 !py-1.5 text-xs" onClick={() => { setError(null); setOk(null); setDraft({ ...r }) }}>{t('edit')}</Button>
                  <Button variant="secondary" className="!px-3 !py-1.5 text-xs text-red-600" onClick={() => remove(r)}><Trash2 className="h-3.5 w-3.5" /></Button>
                </div>
              )}
            </Card>
          ))}
          {!roles.isLoading && !(roles.data ?? []).length && (
            <Card className="md:col-span-2 xl:col-span-3"><p className="text-center text-slate-500">{t('re.roles.none')}</p></Card>
          )}
        </div>
      )}

      {tab === 'roles' && draft && (
        <Card>
          <div className="grid gap-4 md:grid-cols-3">
            <Input label={t('re.roles.name_ar')} value={draft.name_ar} onChange={(e) => setDraft({ ...draft, name_ar: e.target.value })} required />
            <Input label={t('re.roles.name_en')} value={draft.name_en} onChange={(e) => setDraft({ ...draft, name_en: e.target.value })} required dir="ltr" />
            <SelectField label={t('re.roles.scope')} value={draft.data_scope} onChange={(v) => setDraft({ ...draft, data_scope: v })} required
              options={(catalog.data?.data_scopes ?? []).map((s) => ({ value: s.key, label: label(s) }))} />
          </div>
          <h3 className="mt-6 mb-2 font-semibold text-slate-800">{t('re.roles.matrix')}</h3>
          <p className="mb-3 text-xs text-slate-500">{t('re.roles.matrix_help')}</p>
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-50">
                <tr>
                  <th className="p-2 text-start">{t('re.roles.module')}</th>
                  {actions.map((a) => <th key={a.key} className="p-2 text-center font-medium">{label(a)}</th>)}
                </tr>
              </thead>
              <tbody>
                {modules.map((m) => (
                  <tr key={m.key} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="p-2">
                      <button type="button" className="text-start font-medium text-slate-800 hover:text-primary-700" onClick={() => toggleRow(m.key)}>{label(m)}</button>
                      {m.pages.length > 0 && <p className="text-[10px] text-slate-400">{m.pages.map(label).join(' · ')}</p>}
                    </td>
                    {actions.map((a) => {
                      const grantable = perms.can(m.key, a.key)
                      return (
                        <td key={a.key} className="p-2 text-center">
                          <input type="checkbox" aria-label={`${label(m)} — ${label(a)}`} disabled={!grantable}
                            checked={(draft.permissions[m.key] ?? []).includes(a.key)} onChange={() => toggle(m.key, a.key)} />
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3 className="mt-6 mb-2 font-semibold text-slate-800">{t('re.roles.fields')}</h3>
          <div className="flex flex-wrap gap-3">
            {(catalog.data?.field_groups ?? []).map((g) => (
              <label key={g.key} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <input type="checkbox" disabled={!perms.sees(g.key)} checked={draft.field_access.includes(g.key)}
                  onChange={(e) => setDraft({ ...draft, field_access: e.target.checked ? [...draft.field_access, g.key] : draft.field_access.filter((x) => x !== g.key) })} />
                {label(g)}
              </label>
            ))}
          </div>
          <label className="mt-4 flex items-center gap-2 text-sm">
            <input type="checkbox" checked={draft.is_active} onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })} />{t('re.active')}
          </label>
          <div className="mt-6 flex gap-3">
            <Button onClick={save} loading={busy} disabled={!draft.name_ar || !draft.name_en}><Save className="me-2 h-4 w-4" />{t('save')}</Button>
            <Button variant="secondary" onClick={() => setDraft(null)}>{t('cancel')}</Button>
          </div>
        </Card>
      )}

      {tab === 'assign' && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <ul className="divide-y divide-slate-100">
              {(users.data ?? []).filter((u) => !['customer', 'broker'].includes(u.system_role)).map((u) => (
                <li key={u.id}>
                  <button type="button" className={`flex w-full items-center justify-between gap-2 px-2 py-2.5 text-start text-sm ${assignUser === u.id ? 'bg-primary-50' : 'hover:bg-slate-50'}`}
                    onClick={() => { setAssignUser(u.id); setAssignIds(null); setOk(null); setError(null) }}>
                    <span><span className="font-medium">{i18n.language === 'ar' ? u.full_name_ar : u.full_name_en}</span><br /><span className="text-xs text-slate-500">{u.email}</span></span>
                    <UserCog className="h-4 w-4 text-slate-400" />
                  </button>
                </li>
              ))}
            </ul>
          </Card>
          <Card className="lg:col-span-2">
            {!assignUser ? <p className="text-slate-500">{t('re.roles.pick_user')}</p> : !assignment.data ? <p className="text-slate-500">{t('loading')}</p> : (() => {
              const selected = assignIds ?? assignment.data.role_ids
              const eff = assignment.data.effective
              return (
                <div className="space-y-4">
                  <p className="text-sm text-slate-600">{t('re.roles.system_role')}: <Badge>{t(`re.system_role.${assignment.data.system_role}`, { defaultValue: assignment.data.system_role })}</Badge></p>
                  <div className="flex flex-wrap gap-2">
                    {(roles.data ?? []).map((r) => (
                      <label key={r.id} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                        <input type="checkbox" disabled={!canManage} checked={selected.includes(r.id)}
                          onChange={(e) => setAssignIds(e.target.checked ? [...selected, r.id] : selected.filter((x) => x !== r.id))} />
                        {i18n.language === 'ar' ? r.name_ar : r.name_en}
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500">{t('re.roles.no_roles_note')}</p>
                  {canManage && <Button onClick={saveAssignment} loading={busy} disabled={assignIds === null}><Save className="me-2 h-4 w-4" />{t('save')}</Button>}
                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="mb-2 flex items-center gap-2 font-semibold text-slate-800"><ShieldCheck className="h-4 w-4" />{t('re.roles.effective')}</p>
                    <p className="mb-2 text-xs text-slate-500">{t('re.roles.scope')}: {t(`re.scope.${eff.data_scope}`)} · {t('re.roles.fields')}: {eff.field_access.map((f) => label((catalog.data?.field_groups ?? []).find((g) => g.key === f) ?? { key: f, name_ar: f, name_en: f })).join('، ') || '—'}</p>
                    <ul className="space-y-1 text-xs">
                      {Object.entries(eff.permissions).map(([m, acts]) => (
                        <li key={m} className="flex flex-wrap gap-1"><span className="min-w-[8rem] font-medium">{label((catalog.data?.modules ?? []).find((x) => x.key === m) ?? { key: m, name_ar: m, name_en: m })}</span>
                          {acts.map((a) => <Badge key={a} tone="blue">{label(actions.find((x) => x.key === a) ?? { key: a, name_ar: a, name_en: a })}</Badge>)}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )
            })()}
          </Card>
        </div>
      )}

      {tab === 'audit' && (
        <Card>
          <ul className="divide-y divide-slate-100 text-sm">
            {(audit.data ?? []).map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <span className="flex items-center gap-2"><History className="h-4 w-4 text-slate-400" />{t(`re.audit.${a.action}`, { defaultValue: a.action })}{a.entity_id ? ` #${a.entity_id}` : ''}</span>
                <span className="text-xs text-slate-500">{a.user ?? '—'} · {new Date(a.created_at).toLocaleString(i18n.language === 'ar' ? 'ar-EG' : 'en-GB')}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Modal open={templateOpen} onClose={() => setTemplateOpen(false)} title={t('re.roles.from_template')}>
        <div className="space-y-4">
          <ErrorNote message={error} />
          <SelectField label={t('re.roles.template')} value={template} onChange={setTemplate} required options={(catalog.data?.templates ?? []).map((x) => ({ value: x.key, label: label(x) }))} />
          <div className="flex gap-3"><Button onClick={fromTemplate} loading={busy} disabled={!template}>{t('re.confirm')}</Button><Button variant="secondary" onClick={() => setTemplateOpen(false)}>{t('cancel')}</Button></div>
        </div>
      </Modal>
    </div>
  )
}
