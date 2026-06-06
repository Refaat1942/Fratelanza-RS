import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import api from '@/lib/api'

export function useDeleteEntity(endpoint: string, queryKeys: string[]) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`${endpoint}/${id}`)
    },
    onSuccess: () => {
      queryKeys.forEach((key) => qc.invalidateQueries({ queryKey: [key] }))
    },
    onError: () => {
      alert(t('delete_failed'))
    },
  })
}

export function confirmDelete(t: (key: string) => string): boolean {
  return window.confirm(t('confirm_delete'))
}
