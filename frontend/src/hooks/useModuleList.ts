import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export function useModuleList<T>(queryKey: string, endpoint: string) {
  return useQuery({
    queryKey: [queryKey],
    queryFn: async () => {
      const { data } = await api.get<T>(endpoint)
      return data
    },
  })
}
