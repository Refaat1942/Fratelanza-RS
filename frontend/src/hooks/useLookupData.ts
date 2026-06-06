import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Customer, Paginated } from '@/types'

export function useCustomersLookup() {
  return useQuery({
    queryKey: ['customers-lookup'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Customer>>('/customers', { params: { page_size: 100 } })
      return data.items
    },
  })
}

export function useProjectsLookup() {
  return useQuery({
    queryKey: ['projects-lookup'],
    queryFn: async () => {
      const { data } = await api.get<{ items: Record<string, unknown>[] }>('/projects', { params: { page_size: 100 } })
      return data.items
    },
  })
}

export function useUnitsLookup(availableOnly = false) {
  return useQuery({
    queryKey: ['units-lookup', availableOnly],
    queryFn: async () => {
      const { data } = await api.get<Record<string, { id: number; unit_code: string; price: number }[]>>('/projects/units/board')
      const units = Object.entries(data).flatMap(([status, list]) =>
        list.map((u) => ({ ...u, status })),
      )
      return availableOnly ? units.filter((u) => u.status === 'available') : units
    },
  })
}

export function useFloorsLookup(projectId?: number) {
  return useQuery({
    queryKey: ['floors-lookup', projectId],
    queryFn: async () => {
      const { data } = await api.get<Record<string, unknown>[]>('/projects/floors', {
        params: projectId ? { project_id: projectId } : {},
      })
      return data
    },
  })
}

export function useWarehousesLookup() {
  return useQuery({
    queryKey: ['warehouses-lookup'],
    queryFn: async () => {
      const { data } = await api.get<Record<string, unknown>[]>('/warehouse')
      return data
    },
  })
}
