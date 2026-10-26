import type { TFunction } from 'i18next'

/** Turn an API error into a translated, human message (Arabic-first). */
export function apiErrorMessage(err: unknown, t: TFunction): string {
  const res = (err as { response?: { status?: number; data?: { detail?: unknown } } })?.response
  const detail = res?.data?.detail
  if (res?.status === 403) {
    if (typeof detail === 'string' && detail.startsWith('demo_')) return t(`re.errors.${detail}`)
    return t('re.errors.forbidden')
  }
  if (res?.status === 404) return t('re.errors.not_found')
  if (res?.status === 409) return typeof detail === 'string' ? `${t('re.errors.conflict')}: ${detail}` : t('re.errors.conflict')
  if (res?.status === 422) return t('re.errors.validation')
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'code' in (detail as Record<string, unknown>)) return t('re.errors.forbidden')
  return t('re.errors.generic')
}
