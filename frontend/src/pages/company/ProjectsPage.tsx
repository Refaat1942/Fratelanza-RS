import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Building2, LayoutGrid, List, Plus, Home } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { StatCard } from '@/components/ui/StatCard'
import { useModuleList } from '@/hooks/useModuleList'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { Button } from '@/components/ui/Button'
import { UnitsBoard } from '@/components/real-estate/UnitsBoard'
import { ProjectFormModal, UnitFormModal, ReservationFormModal } from '@/components/forms/ModuleFormModals'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'overview' | 'board' | 'projects' | 'units'

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

export function ProjectsPage() {
  const { t } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const [tab, setTab] = useState<Tab>('overview')
  const modal = useCrudModal()
  const [unitOpen, setUnitOpen] = useState(false)
  const [reserveUnitId, setReserveUnitId] = useState<number | undefined>()
  const [reservationOpen, setReservationOpen] = useState(false)
  const deleteProject = useDeleteEntity('/projects', ['projects'])
  const deleteUnit = useDeleteEntity('/projects/units', ['units-board', 'units-lookup'])

  const { data: projectData, isLoading, refetch } = useModuleList<{ items: Record<string, unknown>[] }>('projects', '/projects')
  const projects = projectData?.items ?? []

  const { data: board } = useQuery({
    queryKey: ['units-board'],
    queryFn: async () => (await api.get<Record<string, unknown[]>>('/projects/units/board')).data,
  })

  const boardStats = {
    available: board?.available?.length ?? 0,
    reserved: board?.reserved?.length ?? 0,
    contracted: (board?.contracted?.length ?? 0) + (board?.sold?.length ?? 0),
    total: Object.values(board ?? {}).reduce((s, u) => s + (u as unknown[]).length, 0),
  }

  const allUnits = Object.entries(board ?? {}).flatMap(([status, units]) =>
    (units as Record<string, unknown>[]).map((u) => ({ ...u, status })),
  )

  const tabs: { key: Tab; label: string; icon: typeof Building2 }[] = [
    { key: 'overview', label: t('overview'), icon: Building2 },
    { key: 'board', label: t('units_board'), icon: LayoutGrid },
    { key: 'projects', label: t('projects_list'), icon: List },
    { key: 'units', label: t('units'), icon: Home },
  ]

  return (
    <div>
      <PageHeader
        title={t('projects')}
        subtitle={t('projects_help')}
        icon={Building2}
        accentIndex={2}
        actions={
          <>
            <Button variant="secondary" onClick={() => setUnitOpen(true)}>
              <Plus className="me-2 h-4 w-4" />{t('add_unit')}
            </Button>
            <Button onClick={modal.openCreate}>
              <Plus className="me-2 h-4 w-4" />{t('add_project')}
            </Button>
          </>
        }
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition',
              tab === key ? 'bg-primary-700 text-white shadow-sm' : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50',
            )}
          >
            <Icon className="h-4 w-4" />{label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title={t('projects')} value={formatInteger(projects.length)} icon={Building2} />
            <StatCard title={t('available_units')} value={formatInteger(boardStats.available)} icon={Home} color="bg-emerald-50 text-emerald-700" />
            <StatCard title={t('reserved_units')} value={formatInteger(boardStats.reserved)} icon={Home} color="bg-amber-50 text-amber-700" />
            <StatCard title={t('total_units')} value={formatInteger(boardStats.total)} icon={Home} color="bg-blue-50 text-blue-700" />
          </div>
          <UnitsBoard onUnitClick={(unitId) => { setReserveUnitId(unitId); setReservationOpen(true) }} />
        </>
      )}

      {tab === 'board' && (
        <UnitsBoard onUnitClick={(unitId) => { setReserveUnitId(unitId); setReservationOpen(true) }} />
      )}

      {tab === 'projects' && (
        <DataTable
          title={t('projects_list')}
          loading={isLoading}
          exportFilename="projects"
          data={projects}
          emptyActionLabel={t('add_project')}
          onEmptyAction={modal.openCreate}
          columns={[
            { key: 'code', label: 'Code' },
            { key: 'name_ar', label: t('name_ar') },
            { key: 'name_en', label: t('name_en') },
            { key: 'city', label: t('city') },
            { key: 'status', label: t('status') },
            { key: 'total_units', label: t('units') },
            { key: 'available_units', label: t('available_units') },
          ]}
          rowActions={(row) => (
            <RowActions
              onEdit={() => modal.openEdit(row)}
              onDelete={() => confirmDelete(t) && deleteProject.mutate(row.id as number, { onSuccess: () => { refetch() } })}
            />
          )}
        />
      )}

      {tab === 'units' && (
        <DataTable
          title={t('units')}
          exportFilename="units"
          data={allUnits}
          columns={[
            { key: 'unit_code', label: 'Code' },
            { key: 'unit_number', label: '#' },
            { key: 'unit_type', label: 'Type' },
            { key: 'status', label: t('status') },
            { key: 'area_sqm', label: 'm²' },
            { key: 'price', label: t('price') },
          ]}
          rowActions={(row) => (
            <RowActions
              onDelete={() => confirmDelete(t) && deleteUnit.mutate(row.id as number)}
              extra={
                row.status === 'available' ? (
                  <Button variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={() => { setReserveUnitId(row.id as number); setReservationOpen(true) }}>
                    {t('reserve_unit')}
                  </Button>
                ) : undefined
              }
            />
          )}
        />
      )}

      <ProjectFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />
      <UnitFormModal open={unitOpen} onClose={() => setUnitOpen(false)} />
      <ReservationFormModal open={reservationOpen} onClose={() => { setReservationOpen(false); setReserveUnitId(undefined) }} preselectedUnitId={reserveUnitId} />
    </div>
  )
}
