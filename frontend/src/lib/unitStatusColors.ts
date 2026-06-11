/** Master-plan color tokens — Green = Available, Yellow = Reserved, Red = Sold family */

export type UnitStatusKey =
  | 'available'
  | 'reserved'
  | 'contracted'
  | 'sold'
  | 'delivered'
  | 'blocked'

export interface StatusColorSet {
  fill: string
  fillHover: string
  border: string
  text: string
  legend: string
  labelKey: string
}

export const MASTER_PLAN_STATUS_COLORS: Record<UnitStatusKey, StatusColorSet> = {
  available: {
    fill: 'bg-emerald-500',
    fillHover: 'hover:bg-emerald-400',
    border: 'border-emerald-700',
    text: 'text-white',
    legend: 'bg-emerald-500',
    labelKey: 'master_plan_available',
  },
  reserved: {
    fill: 'bg-amber-400',
    fillHover: 'hover:bg-amber-300',
    border: 'border-amber-600',
    text: 'text-amber-950',
    legend: 'bg-amber-400',
    labelKey: 'master_plan_reserved',
  },
  contracted: {
    fill: 'bg-red-500',
    fillHover: 'hover:bg-red-400',
    border: 'border-red-700',
    text: 'text-white',
    legend: 'bg-red-500',
    labelKey: 'master_plan_contracted',
  },
  sold: {
    fill: 'bg-red-600',
    fillHover: 'hover:bg-red-500',
    border: 'border-red-800',
    text: 'text-white',
    legend: 'bg-red-600',
    labelKey: 'master_plan_sold',
  },
  delivered: {
    fill: 'bg-red-800',
    fillHover: 'hover:bg-red-700',
    border: 'border-red-950',
    text: 'text-white',
    legend: 'bg-red-800',
    labelKey: 'master_plan_delivered',
  },
  blocked: {
    fill: 'bg-slate-400',
    fillHover: 'hover:bg-slate-300',
    border: 'border-slate-600',
    text: 'text-white',
    legend: 'bg-slate-400',
    labelKey: 'master_plan_blocked',
  },
}

export const MASTER_PLAN_LEGEND_ORDER: UnitStatusKey[] = [
  'available',
  'reserved',
  'contracted',
  'sold',
  'delivered',
  'blocked',
]

export function statusColors(status: string): StatusColorSet {
  return MASTER_PLAN_STATUS_COLORS[status as UnitStatusKey] ?? MASTER_PLAN_STATUS_COLORS.blocked
}
