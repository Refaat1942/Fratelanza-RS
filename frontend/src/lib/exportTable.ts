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

export function exportRowsToCsv(rows: Record<string, unknown>[], filename: string) {
  if (!rows.length) return
  const headers = Object.keys(rows[0])
  const csv = [
    headers.join(','),
    ...rows.map((row) =>
      headers.map((h) => `"${String(row[h] ?? '').replace(/"/g, '""')}"`).join(','),
    ),
  ].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  downloadBlob(blob, `${filename}.csv`)
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
