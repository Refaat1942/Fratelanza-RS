import { useModuleList } from '@/hooks/useModuleList'

export function useListData<T>(key: string, endpoint: string) {
  const { data, isLoading, refetch } = useModuleList<T[] | { items: T[] }>(key, endpoint)
  const items = Array.isArray(data) ? data : (data as { items?: T[] })?.items ?? []
  return { items, isLoading, refetch }
}
