import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, Plus, CheckCircle } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { ReportLinkButton } from '@/components/ui/ReportLinkButton'
import { useListData } from '@/hooks/useListData'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { Button } from '@/components/ui/Button'
import { BrokerFormModal } from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'brokers' | 'commissions'

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

export function BrokersPage() {
  const { t, i18n } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('brokers')
  const modal = useCrudModal()
  const deleteBroker = useDeleteEntity('/brokers', ['brokers'])
  const { items: brokers, isLoading: brokersLoading, refetch } = useListData<Record<string, unknown>>('brokers', '/brokers')
  const { items: commissions, isLoading: commissionsLoading, refetch: refetchCommissions } = useListData<Record<string, unknown>>('broker-commissions', '/brokers/commissions')

  const approveCommission = useMutation({
    mutationFn: (id: number) => api.post(`/brokers/commissions/${id}/approve`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['broker-commissions'] })
      refetchCommissions()
    },
  })

  const tabs: { key: Tab; label: string }[] = [
    { key: 'brokers', label: t('brokers') },
    { key: 'commissions', label: t('commissions') },
  ]

  return (
    <div>
      <PageHeader
        title={t('brokers')}
        subtitle={t('brokers_help')}
        icon={Users}
        accentIndex={3}
        actions={
          <>
            <ReportLinkButton reportKey="broker_performance" />
            {tab === 'brokers' && (
              <Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_broker')}</Button>
            )}
          </>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={cn(
              'rounded-lg px-3 py-1.5 text-sm font-medium',
              tab === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'brokers' && (
        <DataTable
          title={t('brokers')}
          loading={brokersLoading}
          exportFilename="brokers"
          data={brokers}
          columns={[
            { key: 'name_ar', label: t('brokers'), render: (row) => String(i18n.language === 'ar' ? row.name_ar : row.name_en) },
            { key: 'mobile', label: t('mobile') },
            { key: 'commission_rate', label: t('commission_rate') },
            { key: 'rank_score', label: t('rank') },
          ]}
          rowActions={(row) => (
            <RowActions
              onEdit={() => modal.openEdit(row)}
              onDelete={() => confirmDelete(t) && deleteBroker.mutate(row.id as number, { onSuccess: () => refetch() })}
            />
          )}
        />
      )}

      {tab === 'commissions' && (
        <DataTable
          title={t('commissions')}
          loading={commissionsLoading}
          exportFilename="commissions"
          data={commissions}
          columns={[
            { key: 'broker_name', label: t('brokers') },
            { key: 'amount', label: t('amount'), render: (row) => formatEGP(row.amount as number) },
            { key: 'contract_id', label: t('contracts') },
            { key: 'status', label: t('status') },
          ]}
          rowActions={(row) => (
            <RowActions
              extra={
                row.status === 'pending' ? (
                  <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => approveCommission.mutate(row.id as number)} title={t('approve')}>
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                  </Button>
                ) : undefined
              }
            />
          )}
        />
      )}

      <BrokerFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}
