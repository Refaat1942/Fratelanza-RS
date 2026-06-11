import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Grid3x3, Map, X, Home, CircleCheck, Clock, CircleX } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatCard } from '@/components/ui/StatCard'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'
import {
  MASTER_PLAN_LEGEND_ORDER,
  MASTER_PLAN_STATUS_COLORS,
  statusColors,
} from '@/lib/unitStatusColors'

interface MasterPlanUnit {
  id: number
  unit_code: string
  unit_number: string
  unit_type: string
  status: string
  price: number
  area_sqm: number
  bedrooms: number
}

interface MasterPlanFloor {
  id: number
  floor_number: number
  name_en: string | null
  name_ar: string | null
  units: MasterPlanUnit[]
}

interface MasterPlanBuilding {
  id: number
  code: string
  name_en: string
  name_ar: string
  floors: MasterPlanFloor[]
}

interface MasterPlanData {
  project: {
    id: number
    code: string
    name_en: string
    name_ar: string
    city: string | null
  }
  buildings: MasterPlanBuilding[]
  stats: {
    total: number
    available: number
    reserved: number
    sold: number
    by_status: Record<string, number>
  }
}

type ViewMode = 'grid' | 'map'

interface MasterPlanDashboardProps {
  projectId: number | null
  projects: Array<{ id: number; name_en?: string; name_ar?: string }>
  onProjectChange: (id: number) => void
  onReserveUnit?: (unitId: number) => void
}

export function MasterPlanDashboard({
  projectId,
  projects,
  onProjectChange,
  onReserveUnit,
}: MasterPlanDashboardProps) {
  const { t, i18n } = useTranslation()
  const { formatEGP, formatInteger, localizeDigits } = useFormatNumber()
  const [view, setView] = useState<ViewMode>('grid')
  const [selected, setSelected] = useState<MasterPlanUnit | null>(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['master-plan', projectId],
    queryFn: async () =>
      (await api.get<MasterPlanData>(`/projects/${projectId}/master-plan`)).data,
    enabled: !!projectId,
  })

  const legendItems = useMemo(() => {
    if (!data) return []
    return MASTER_PLAN_LEGEND_ORDER.filter((key) => (data.stats.by_status[key] ?? 0) > 0)
  }, [data])

  if (!projectId) {
    return (
      <EmptyState
        title={t('master_plan_select_project')}
        description={t('master_plan_select_project_help')}
      />
    )
  }

  if (isLoading) return <LoadingState />

  if (!data || data.buildings.length === 0) {
    return (
      <EmptyState
        title={t('master_plan_no_units')}
        description={t('master_plan_no_units_help')}
      />
    )
  }

  const projectName = i18n.language === 'ar' ? data.project.name_ar : data.project.name_en

  const renderUnitCell = (unit: MasterPlanUnit, compact = false) => {
    const colors = statusColors(unit.status)
    return (
      <button
        key={unit.id}
        type="button"
        title={`${unit.unit_code} — ${unit.status}`}
        onClick={() => setSelected(unit)}
        className={cn(
          'relative flex flex-col items-center justify-center rounded-lg border-2 shadow-sm transition-all',
          colors.fill,
          colors.fillHover,
          colors.border,
          colors.text,
          compact ? 'min-h-[52px] min-w-[52px] p-1.5 text-[10px]' : 'min-h-[72px] min-w-[80px] p-2 text-xs',
          selected?.id === unit.id && 'ring-2 ring-primary-300 ring-offset-2 scale-105 z-10',
          'hover:scale-105 hover:shadow-md hover:z-10',
        )}
      >
        <span className="font-bold leading-tight">{unit.unit_code}</span>
        {!compact && (
          <span className="mt-0.5 opacity-90">{localizeDigits(unit.unit_number)}</span>
        )}
      </button>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-slate-700">{t('projects')}</label>
          <select
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
            value={projectId}
            onChange={(e) => onProjectChange(Number(e.target.value))}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {i18n.language === 'ar' ? p.name_ar : p.name_en}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <Button
            variant={view === 'grid' ? 'primary' : 'secondary'}
            onClick={() => setView('grid')}
          >
            <Grid3x3 className="me-2 h-4 w-4" />
            {t('master_plan_grid_view')}
          </Button>
          <Button
            variant={view === 'map' ? 'primary' : 'secondary'}
            onClick={() => setView('map')}
          >
            <Map className="me-2 h-4 w-4" />
            {t('master_plan_map_view')}
          </Button>
          <Button variant="secondary" onClick={() => refetch()}>
            {t('master_plan_refresh')}
          </Button>
        </div>
      </div>

      <p className="text-sm text-slate-500">{t('master_plan_help')}</p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={t('total_units')}
          value={formatInteger(data.stats.total)}
          icon={Home}
          color="bg-slate-50 text-slate-700"
        />
        <StatCard
          title={t('master_plan_available')}
          value={formatInteger(data.stats.available)}
          icon={CircleCheck}
          color="bg-emerald-50 text-emerald-700"
        />
        <StatCard
          title={t('master_plan_reserved')}
          value={formatInteger(data.stats.reserved)}
          icon={Clock}
          color="bg-amber-50 text-amber-700"
        />
        <StatCard
          title={t('master_plan_sold')}
          value={formatInteger(data.stats.sold)}
          icon={CircleX}
          color="bg-red-50 text-red-700"
        />
      </div>

      <Card className="!p-4">
        <p className="mb-3 text-sm font-semibold text-slate-800">{t('master_plan_legend')}</p>
        <div className="flex flex-wrap gap-3">
          {legendItems.map((key) => {
            const meta = MASTER_PLAN_STATUS_COLORS[key]
            const count = data.stats.by_status[key] ?? 0
            return (
              <div key={key} className="flex items-center gap-2 text-sm text-slate-700">
                <span className={cn('h-4 w-4 rounded border border-black/10', meta.legend)} />
                <span>{t(meta.labelKey)}</span>
                <span className="text-slate-400">({formatInteger(count)})</span>
              </div>
            )
          })}
        </div>
      </Card>

      {view === 'grid' ? (
        <div className="space-y-8">
          {data.buildings.map((building) => (
            <Card key={building.id} className="overflow-hidden !p-0">
              <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
                <h3 className="font-semibold text-slate-900">
                  {i18n.language === 'ar' ? building.name_ar : building.name_en}{' '}
                  <span className="text-slate-500">({building.code})</span>
                </h3>
              </div>
              <div className="divide-y divide-slate-100">
                {building.floors.map((floor) => (
                  <div
                    key={floor.id}
                    className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center"
                  >
                    <div className="w-full shrink-0 sm:w-28">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        {t('master_plan_floor')}
                      </p>
                      <p className="text-lg font-bold text-slate-800">
                        {localizeDigits(String(floor.floor_number))}
                      </p>
                      {(floor.name_en || floor.name_ar) && (
                        <p className="text-xs text-slate-500">
                          {i18n.language === 'ar' ? floor.name_ar : floor.name_en}
                        </p>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {floor.units.length === 0 ? (
                        <span className="text-sm text-slate-400">{t('no_data')}</span>
                      ) : (
                        floor.units.map((u) => renderUnitCell(u))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
          {data.buildings.map((building) => (
            <Card
              key={building.id}
              className="relative overflow-hidden !p-0 ring-1 ring-slate-200"
            >
              <div className="bg-gradient-to-br from-primary-800 to-primary-600 px-4 py-3 text-white">
                <p className="text-xs uppercase tracking-wide opacity-80">{projectName}</p>
                <h3 className="text-lg font-bold">
                  {i18n.language === 'ar' ? building.name_ar : building.name_en}
                </h3>
              </div>
              <div className="space-y-1 bg-slate-100 p-4">
                {building.floors.map((floor) => (
                  <div
                    key={floor.id}
                    className="flex items-center gap-2 rounded-md bg-white/80 px-2 py-1.5"
                  >
                    <span className="w-8 shrink-0 text-center text-xs font-bold text-slate-500">
                      {localizeDigits(String(floor.floor_number))}
                    </span>
                    <div className="flex flex-1 flex-wrap gap-1">
                      {floor.units.map((u) => renderUnitCell(u, true))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center">
          <Card className="relative w-full max-w-md animate-fade-in-up !p-6 shadow-xl">
            <button
              type="button"
              className="absolute end-4 top-4 rounded-lg p-1 text-slate-400 hover:bg-slate-100"
              onClick={() => setSelected(null)}
            >
              <X className="h-5 w-5" />
            </button>
            <div className="mb-4 flex items-center gap-3">
              <span
                className={cn(
                  'h-10 w-10 rounded-lg border-2',
                  statusColors(selected.status).fill,
                  statusColors(selected.status).border,
                )}
              />
              <div>
                <h3 className="text-xl font-bold text-slate-900">{selected.unit_code}</h3>
                <p className="text-sm capitalize text-slate-500">
                  {t(statusColors(selected.status).labelKey)}
                </p>
              </div>
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-slate-500">{t('units')}</dt>
                <dd className="font-medium">#{localizeDigits(selected.unit_number)}</dd>
              </div>
              <div>
                <dt className="text-slate-500">{t('price')}</dt>
                <dd className="font-medium">{formatEGP(selected.price)}</dd>
              </div>
              <div>
                <dt className="text-slate-500">m²</dt>
                <dd className="font-medium">{selected.area_sqm}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Type</dt>
                <dd className="font-medium capitalize">{selected.unit_type}</dd>
              </div>
            </dl>
            {selected.status === 'available' && onReserveUnit && (
              <Button className="mt-6 w-full" onClick={() => { onReserveUnit(selected.id); setSelected(null) }}>
                {t('reserve_unit')}
              </Button>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
