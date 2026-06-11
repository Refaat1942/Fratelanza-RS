import { useState, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { LayoutGrid, GanttChart, ListTodo, Plus } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/ui/PageHeader'
import { RowActions } from '@/components/ui/RowActions'
import { ConstructionGantt } from '@/components/construction/ConstructionGantt'
import { ConstructionPhaseFormModal, ConstructionTaskFormModal } from '@/components/forms/ModuleFormModals'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { useProjectsLookup } from '@/hooks/useLookupData'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'phases' | 'tasks' | 'gantt'

function useCrudModal() {
  const [open, setOpen] = useState(false)
  const [editRow, setEditRow] = useState<Record<string, unknown> | null>(null)
  const openCreate = useCallback(() => { setEditRow(null); setOpen(true) }, [])
  const openEdit = useCallback((row: Record<string, unknown>) => { setEditRow(row); setOpen(true) }, [])
  const close = useCallback(() => { setOpen(false); setEditRow(null) }, [])
  return { open, editRow, openCreate, openEdit, close }
}

export function ConstructionPage() {
  const { t, i18n } = useTranslation()
  const { formatEGP, formatInteger } = useFormatNumber()
  const qc = useQueryClient()
  const { data: projects = [] } = useProjectsLookup()
  const [tab, setTab] = useState<Tab>('gantt')
  const [projectId, setProjectId] = useState('')
  const phaseModal = useCrudModal()
  const taskModal = useCrudModal()
  const deletePhase = useDeleteEntity('/construction/phases', ['phases', 'construction-tasks', 'construction-schedule'])
  const deleteTask = useDeleteEntity('/construction/tasks', ['construction-tasks', 'phases', 'construction-schedule'])

  const effectiveProjectId = projectId || (projects[0] ? String(projects[0].id) : '')

  const { data: phases = [], isLoading: phasesLoading, refetch: refetchPhases } = useQuery({
    queryKey: ['phases', effectiveProjectId],
    queryFn: async () => {
      const { data } = await api.get('/construction/phases', {
        params: effectiveProjectId ? { project_id: effectiveProjectId } : {},
      })
      return data
    },
    enabled: !!effectiveProjectId || projects.length > 0,
  })

  const { data: tasks = [], isLoading: tasksLoading, refetch: refetchTasks } = useQuery({
    queryKey: ['construction-tasks', effectiveProjectId],
    queryFn: async () => {
      const { data } = await api.get('/construction/tasks', {
        params: effectiveProjectId ? { project_id: effectiveProjectId } : {},
      })
      return data
    },
    enabled: !!effectiveProjectId,
  })

  const { data: schedule, isLoading: scheduleLoading } = useQuery({
    queryKey: ['construction-schedule', effectiveProjectId],
    queryFn: async () => (await api.get('/construction/schedule', { params: { project_id: effectiveProjectId } })).data,
    enabled: !!effectiveProjectId && tab === 'gantt',
  })

  const updatePhaseProgress = useMutation({
    mutationFn: ({ id, progress_percent }: { id: number; progress_percent: number }) =>
      api.patch(`/construction/phases/${id}/progress`, { progress_percent }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['phases'] })
      qc.invalidateQueries({ queryKey: ['construction-schedule'] })
    },
  })

  const phaseLabel = (p: Record<string, unknown>) =>
    i18n.language === 'ar' ? String(p.name_ar) : String(p.name_en ?? p.name_ar)

  return (
    <div>
      <PageHeader
        title={t('construction')}
        subtitle={t('construction_help')}
        icon={GanttChart}
        accentIndex={5}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <select
              className="input-field min-w-[180px]"
              value={effectiveProjectId}
              onChange={(e) => setProjectId(e.target.value)}
            >
              {projects.map((p) => (
                <option key={String(p.id)} value={String(p.id)}>{String(p.name_ar)}</option>
              ))}
            </select>
            {tab === 'phases' && (
              <Button onClick={phaseModal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_phase')}</Button>
            )}
            {tab === 'tasks' && (
              <Button onClick={taskModal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_task')}</Button>
            )}
          </div>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {[
          { key: 'gantt' as const, label: t('gantt_timeline'), icon: GanttChart },
          { key: 'phases' as const, label: t('phases'), icon: LayoutGrid },
          { key: 'tasks' as const, label: t('tasks'), icon: ListTodo },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium',
              tab === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
            )}
          >
            <Icon className="h-4 w-4" />{label}
          </button>
        ))}
      </div>

      {tab === 'gantt' && (
        <ConstructionGantt
          rows={schedule?.rows ?? []}
          rangeStart={schedule?.range_start ?? new Date().toISOString().slice(0, 10)}
          rangeEnd={schedule?.range_end ?? new Date().toISOString().slice(0, 10)}
          loading={scheduleLoading}
        />
      )}

      {tab === 'phases' && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          {phasesLoading ? (
            <p className="p-6 text-slate-500">{t('loading')}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head-gradient">
                  <th className="px-4 py-3 text-start">{t('construction')}</th>
                  <th className="px-4 py-3 text-start">{t('timeline')}</th>
                  <th className="px-4 py-3 text-start">{t('progress')}</th>
                  <th className="px-4 py-3 text-start">{t('planned_cost')}</th>
                  <th className="px-4 py-3 text-start">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {phases.map((p: Record<string, unknown>) => (
                  <tr key={p.id as number} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-medium">{phaseLabel(p)}</td>
                    <td className="px-4 py-3 text-slate-600 text-xs">
                      {String(p.planned_start ?? '—')} → {String(p.planned_end ?? '—')}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="range"
                          min={0}
                          max={100}
                          value={Number(p.progress_percent ?? 0)}
                          onChange={(e) => updatePhaseProgress.mutate({ id: p.id as number, progress_percent: Number(e.target.value) })}
                          className="w-28 accent-primary-600"
                        />
                        <span className="w-10 text-xs font-medium">{formatInteger(p.progress_percent as number)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">{formatEGP(p.planned_cost as number)}</td>
                    <td className="px-4 py-3">
                      <RowActions
                        onEdit={() => phaseModal.openEdit(p)}
                        onDelete={() => confirmDelete(t) && deletePhase.mutate(p.id as number, { onSuccess: () => refetchPhases() })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'tasks' && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          {tasksLoading ? (
            <p className="p-6 text-slate-500">{t('loading')}</p>
          ) : tasks.length === 0 ? (
            <p className="p-8 text-center text-slate-500">{t('no_tasks_help')}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head-gradient">
                  <th className="px-4 py-3 text-start">{t('tasks')}</th>
                  <th className="px-4 py-3 text-start">{t('phase')}</th>
                  <th className="px-4 py-3 text-start">{t('timeline')}</th>
                  <th className="px-4 py-3 text-start">{t('progress')}</th>
                  <th className="px-4 py-3 text-start">{t('status')}</th>
                  <th className="px-4 py-3 text-start">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task: Record<string, unknown>) => (
                  <tr key={task.id as number} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-medium">
                      {i18n.language === 'ar' ? String(task.name_ar) : String(task.name_en)}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{String(task.phase_name ?? '')}</td>
                    <td className="px-4 py-3 text-xs text-slate-600">
                      {String(task.planned_start ?? '—')} → {String(task.planned_end ?? '—')}
                    </td>
                    <td className="px-4 py-3">{formatInteger(task.progress_percent as number)}%</td>
                    <td className="px-4 py-3 capitalize">{String(task.status)}</td>
                    <td className="px-4 py-3">
                      <RowActions
                        onEdit={() => taskModal.openEdit(task)}
                        onDelete={() => confirmDelete(t) && deleteTask.mutate(task.id as number, { onSuccess: () => refetchTasks() })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <ConstructionPhaseFormModal
        open={phaseModal.open}
        onClose={() => { phaseModal.close(); refetchPhases(); qc.invalidateQueries({ queryKey: ['construction-schedule'] }) }}
        editRow={phaseModal.editRow}
        defaultProjectId={effectiveProjectId}
      />
      <ConstructionTaskFormModal
        open={taskModal.open}
        onClose={() => { taskModal.close(); refetchTasks(); qc.invalidateQueries({ queryKey: ['phases', 'construction-schedule'] }) }}
        editRow={taskModal.editRow}
        projectId={effectiveProjectId}
      />
    </div>
  )
}
