import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { HardHat, Plus } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { ReportLinkButton } from '@/components/ui/ReportLinkButton'
import { useListData } from '@/hooks/useListData'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { Button } from '@/components/ui/Button'
import { ConstructionPhaseFormModal } from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { cn } from '@/lib/utils'

type Tab = 'phases' | 'tasks' | 'milestones'

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

export function ConstructionPage() {
  const { t } = useTranslation()
  const { formatEGP } = useFormatNumber()
  const [tab, setTab] = useState<Tab>('phases')
  const modal = useCrudModal()
  const deletePhase = useDeleteEntity('/construction/phases', ['phases'])
  const { items: phases, isLoading: phasesLoading, refetch } = useListData<Record<string, unknown>>('phases', '/construction/phases')
  const { items: tasks, isLoading: tasksLoading } = useListData<Record<string, unknown>>('construction-tasks', '/construction/tasks')
  const { items: milestones, isLoading: milestonesLoading } = useListData<Record<string, unknown>>('construction-milestones', '/construction/milestones')

  const tabs: { key: Tab; label: string }[] = [
    { key: 'phases', label: t('construction_phases') },
    { key: 'tasks', label: t('construction_tasks') },
    { key: 'milestones', label: t('construction_milestones') },
  ]

  return (
    <div>
      <PageHeader
        title={t('construction')}
        subtitle={t('construction_help')}
        icon={HardHat}
        accentIndex={5}
        actions={
          <>
            <ReportLinkButton reportKey="construction_progress" />
            {tab === 'phases' && (
              <Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_phase')}</Button>
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

      {tab === 'phases' && (
        <DataTable
          title={t('construction_phases')}
          loading={phasesLoading}
          exportFilename="construction-phases"
          data={phases}
          actions={<Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_phase')}</Button>}
          columns={[
            { key: 'project_name', label: t('projects') },
            { key: 'name_ar', label: t('name_ar') },
            { key: 'progress_percent', label: t('progress') },
            { key: 'planned_cost', label: t('planned_cost'), render: (row) => formatEGP(row.planned_cost as number) },
            { key: 'actual_cost', label: t('actual_cost'), render: (row) => formatEGP(row.actual_cost as number) },
          ]}
          rowActions={(row) => (
            <RowActions
              onEdit={() => modal.openEdit(row)}
              onDelete={() => confirmDelete(t) && deletePhase.mutate(row.id as number, { onSuccess: () => refetch() })}
            />
          )}
        />
      )}

      {tab === 'tasks' && (
        <DataTable
          title={t('construction_tasks')}
          loading={tasksLoading}
          exportFilename="construction-tasks"
          data={tasks}
          columns={[
            { key: 'name_ar', label: t('name_ar') },
            { key: 'phase_id', label: t('phase') },
            { key: 'contractor', label: t('contractor') },
            { key: 'progress_percent', label: t('progress') },
            { key: 'status', label: t('status') },
          ]}
        />
      )}

      {tab === 'milestones' && (
        <DataTable
          title={t('construction_milestones')}
          loading={milestonesLoading}
          exportFilename="construction-milestones"
          data={milestones}
          columns={[
            { key: 'name_ar', label: t('name_ar') },
            { key: 'project_id', label: t('projects') },
            { key: 'target_date', label: t('target_date') },
            { key: 'status', label: t('status') },
          ]}
        />
      )}

      <ConstructionPhaseFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
    </div>
  )
}
