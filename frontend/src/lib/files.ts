import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

const API_URL = import.meta.env.VITE_API_URL || ''

/** Tenant files are served only with the bearer token, so fetch them as a blob and open locally. */
export async function openTenantFile(url: string): Promise<void> {
  const token = useAuthStore.getState().accessToken
  const res = await axios.get(`${API_URL}${url}`, { responseType: 'blob', headers: { Authorization: `Bearer ${token}` } })
  window.open(URL.createObjectURL(res.data as Blob), '_blank', 'noopener')
}
