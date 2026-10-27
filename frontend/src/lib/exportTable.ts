import api from './api'

export async function exportRowsToExcel(
  rows: Record<string, unknown>[],
  filename: string,
) {
  if (!rows.length) return
  const { data } = await api.post(
    '/exports/rows',
    { rows, filename },
    { params: { format: 'xlsx' }, responseType: 'blob' },
  )
  downloadBlob(data, `${filename}.xlsx`)
}

function downloadBlob(data: Blob, filename: string) {
  const url = window.URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
