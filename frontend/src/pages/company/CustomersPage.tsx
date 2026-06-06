import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  FileText, MessageCircle, Phone, Upload, UserPlus, Users, ClipboardList, Handshake,
} from 'lucide-react'
import { RowActions } from '@/components/ui/RowActions'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { ReminderFormModal } from '@/components/forms/ReminderFormModal'
import { CustomerImportModal } from '@/components/forms/CustomerImportModal'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { StatCard } from '@/components/ui/StatCard'
import { LoadingState } from '@/components/ui/LoadingState'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { ClientFormModal } from '@/components/forms/ClientFormModal'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { telLink, whatsappLink } from '@/lib/phone'
import { cn } from '@/lib/utils'
import type { Customer, Paginated } from '@/types'

type CustomerRow = Customer & {
  city?: string
  whatsapp?: string
  notes?: string
  contracts_count?: number
  reservations_count?: number
  lead_id?: number
  lead_stage?: string
}

type CustomerProfile = {
  customer: CustomerRow
  lead?: { id: number; stage: string; score: number }
  contracts: { id: number; contract_number: string; status: string; total_price: number }[]
  reservations: { id: number; reservation_number: string; status: string; deposit_amount: number }[]
  timeline: { id: number; activity_type: string; title: string; description?: string; created_at: string }[]
}

export function CustomersPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { formatInteger, formatPhone, formatEGP } = useFormatNumber()
  const [open, setOpen] = useState(false)
  const [editCustomer, setEditCustomer] = useState<CustomerRow | null>(null)
  const [importOpen, setImportOpen] = useState(false)
  const [reminderOpen, setReminderOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [noteText, setNoteText] = useState('')
  const deleteCustomer = useDeleteEntity('/customers', ['customers'])

  const { data: summary } = useQuery({
    queryKey: ['customers-summary'],
    queryFn: async () => (await api.get('/customers/summary')).data,
  })

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<CustomerRow>>('/customers', { params: { page_size: 100 } })
      return data
    },
  })

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['customer-profile', selectedId],
    queryFn: async () => (await api.get<CustomerProfile>(`/customers/${selectedId}/profile`)).data,
    enabled: !!selectedId,
  })

  const addNote = useMutation({
    mutationFn: async () => {
      if (!selectedId || !noteText.trim()) return
      await api.post(`/customers/${selectedId}/notes`, { title: t('customer_note'), description: noteText.trim() })
    },
    onSuccess: () => {
      setNoteText('')
      qc.invalidateQueries({ queryKey: ['customer-profile', selectedId] })
    },
  })

  const filtered = useMemo(() => {
    if (!data?.items || !search) return data?.items ?? []
    const q = search.toLowerCase()
    return data.items.filter((c) =>
      [c.full_name_ar, c.full_name_en, c.mobile, c.email, c.city].some((v) => v?.toLowerCase().includes(q)),
    )
  }, [data, search])

  const selected = profile?.customer
  const displayName = (c: CustomerRow) => (i18n.language === 'ar' ? c.full_name_ar : c.full_name_en)

  return (
    <div>
      <PageHeader
        title={t('customers')}
        subtitle={t('customers_help')}
        icon={Users}
        accentIndex={1}
        actions={
          <>
            <Button variant="secondary" onClick={() => setImportOpen(true)}>
              <Upload className="me-2 h-4 w-4" />
              {t('bulk_import')}
            </Button>
            <Button onClick={() => { setEditCustomer(null); setOpen(true) }}>
              <UserPlus className="me-2 h-4 w-4" />
              {t('add_client')}
            </Button>
          </>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title={t('total_customers')} value={formatInteger(summary?.total)} icon={Users} />
        <StatCard title={t('customers_with_contracts')} value={formatInteger(summary?.with_contracts)} icon={FileText} color="bg-emerald-50 text-emerald-700" />
        <StatCard title={t('customers_with_reservations')} value={formatInteger(summary?.with_reservations)} icon={Handshake} color="bg-amber-50 text-amber-700" />
        <StatCard title={t('customers_with_leads')} value={formatInteger(summary?.with_leads)} icon={ClipboardList} color="bg-violet-50 text-violet-700" />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <div className="mb-4">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('search_table')}
              className="input-field"
            />
          </div>
          {isLoading ? (
            <LoadingState />
          ) : filtered.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500">{t('no_data')}</p>
          ) : (
            <div className="max-h-[32rem] space-y-2 overflow-y-auto">
              {filtered.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setSelectedId(c.id)}
                  className={cn(
                    'w-full rounded-xl border p-3 text-start transition',
                    selectedId === c.id ? 'border-primary-400 bg-primary-50' : 'border-slate-200 bg-white hover:border-primary-200',
                  )}
                >
                  <p className="font-medium text-slate-900">{displayName(c)}</p>
                  <p className="text-xs text-slate-500">{formatPhone(c.mobile)} · {c.city || '—'}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(c.contracts_count ?? 0) > 0 && (
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                        {formatInteger(c.contracts_count)} {t('contracts')}
                      </span>
                    )}
                    {(c.reservations_count ?? 0) > 0 && (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                        {formatInteger(c.reservations_count)} {t('reservations')}
                      </span>
                    )}
                    {c.lead_stage && (
                      <span className="rounded-full bg-violet-50 px-2 py-0.5 text-xs text-violet-700">
                        {c.lead_stage.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card className="lg:col-span-3">
          {!selectedId ? (
            <div className="flex h-64 flex-col items-center justify-center text-center text-slate-500">
              <Users className="mb-3 h-10 w-10 opacity-40" />
              <p className="text-sm">{t('select_customer_profile')}</p>
            </div>
          ) : profileLoading || !selected ? (
            <LoadingState />
          ) : (
            <div className="space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-slate-900">{displayName(selected)}</h2>
                  <p className="text-sm text-slate-500">#{formatInteger(selected.id)} · {selected.city || '—'}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <a href={telLink(selected.mobile)} className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm text-white">
                    <Phone className="h-4 w-4" />{t('call_now')}
                  </a>
                  {(selected.whatsapp || selected.mobile) && (
                    <a href={whatsappLink(selected.whatsapp || selected.mobile)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 rounded-lg bg-green-600 px-3 py-1.5 text-sm text-white">
                      <MessageCircle className="h-4 w-4" />WhatsApp
                    </a>
                  )}
                  <Button variant="secondary" onClick={() => { setEditCustomer(selected); setOpen(true) }}>{t('edit')}</Button>
                  <Button variant="secondary" onClick={() => {
                    setReminderOpen(true)
                  }}>{t('schedule_call')}</Button>
                  <RowActions
                    onDelete={() => confirmDelete(t) && deleteCustomer.mutate(selected.id, {
                      onSuccess: () => { setSelectedId(null); refetch() },
                    })}
                  />
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg bg-slate-50 p-3 text-sm">
                  <p className="text-xs font-medium text-slate-500">{t('mobile')}</p>
                  <p>{formatPhone(selected.mobile)}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3 text-sm">
                  <p className="text-xs font-medium text-slate-500">{t('email')}</p>
                  <p>{selected.email || '—'}</p>
                </div>
              </div>

              {profile.lead && (
                <div className="rounded-xl border border-violet-200 bg-violet-50 p-4">
                  <p className="font-medium text-violet-900">{t('linked_lead')}</p>
                  <p className="text-sm text-violet-700">
                    {t('lead_stage')}: {profile.lead.stage.replace(/_/g, ' ')} · {t('score')}: {profile.lead.score}
                  </p>
                  <Button variant="secondary" className="mt-2" onClick={() => navigate('/leads')}>{t('view_leads')}</Button>
                </div>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="mb-2 font-medium text-slate-900">{t('contracts')} ({profile.contracts.length})</p>
                  {profile.contracts.length === 0 ? (
                    <p className="text-sm text-slate-500">{t('no_customer_contracts')}</p>
                  ) : (
                    <ul className="space-y-2">
                      {profile.contracts.map((c) => (
                        <li key={c.id} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-sm">
                          <button type="button" onClick={() => navigate('/contracts')} className="font-medium text-primary-700 hover:underline">
                            {c.contract_number}
                          </button>
                          <span>{formatEGP(c.total_price)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div>
                  <p className="mb-2 font-medium text-slate-900">{t('reservations')} ({profile.reservations.length})</p>
                  {profile.reservations.length === 0 ? (
                    <p className="text-sm text-slate-500">{t('no_customer_reservations')}</p>
                  ) : (
                    <ul className="space-y-2">
                      {profile.reservations.map((r) => (
                        <li key={r.id} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-sm">
                          <button type="button" onClick={() => navigate('/reservations')} className="font-medium text-primary-700 hover:underline">
                            {r.reservation_number}
                          </button>
                          <span>{formatEGP(r.deposit_amount)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              <div>
                <p className="mb-2 font-medium text-slate-900">{t('customer_timeline')}</p>
                {profile.timeline.length === 0 ? (
                  <p className="text-sm text-slate-500">{t('no_customer_activity')}</p>
                ) : (
                  <ul className="mb-4 max-h-48 space-y-2 overflow-y-auto text-sm">
                    {profile.timeline.map((a) => (
                      <li key={a.id} className="rounded-lg border border-slate-100 px-3 py-2">
                        <p className="font-medium">{a.title}</p>
                        {a.description && <p className="text-slate-500">{a.description}</p>}
                        <p className="text-xs text-slate-400">{a.created_at}</p>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="flex gap-2">
                  <Input
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder={t('add_customer_note_placeholder')}
                  />
                  <Button onClick={() => addNote.mutate()} loading={addNote.isPending} disabled={!noteText.trim()}>
                    {t('add_note')}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>

      <ClientFormModal
        open={open}
        editCustomer={editCustomer}
        onClose={() => { setOpen(false); setEditCustomer(null); refetch(); qc.invalidateQueries({ queryKey: ['customer-profile', selectedId] }); qc.invalidateQueries({ queryKey: ['customers-summary'] }) }}
      />
      <CustomerImportModal open={importOpen} onClose={() => { setImportOpen(false); refetch() }} />
      <ReminderFormModal
        open={reminderOpen}
        onClose={() => setReminderOpen(false)}
        customerId={selectedId ?? undefined}
        defaultTitle={selected ? `${t('schedule_call')}: ${displayName(selected)}` : ''}
      />
    </div>
  )
}
