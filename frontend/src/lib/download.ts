import api from './api'

export async function downloadReport(
  reportKey: string,
  params?: Record<string, string>,
) {
  const { data } = await api.get(`/reports/${reportKey}/export`, {
    params: { format: 'xlsx', ...params },
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${reportKey}.xlsx`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
