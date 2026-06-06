const EGP_FORMATTER = new Intl.NumberFormat('ar-EG', {
  style: 'currency',
  currency: 'EGP',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

export function formatEGP(amount: number | string | null | undefined): string {
  const n = Number(amount ?? 0)
  if (Number.isNaN(n)) return '0 ج.م'
  return EGP_FORMATTER.format(n)
}

export function formatNumber(amount: number | string | null | undefined): string {
  const n = Number(amount ?? 0)
  if (Number.isNaN(n)) return '0'
  return new Intl.NumberFormat('ar-EG').format(n)
}
