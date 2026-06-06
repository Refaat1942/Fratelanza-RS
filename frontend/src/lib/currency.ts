import i18n from '@/i18n'

/** Locale for Intl: Western digits in English, Arabic-Indic digits in Arabic. */
export function getNumberLocale(lang?: string): string {
  const l = lang ?? i18n.language ?? 'ar'
  return l.startsWith('ar') ? 'ar-EG' : 'en-US'
}

const formatters = new Map<string, Intl.NumberFormat>()
const egpFormatters = new Map<string, Intl.NumberFormat>()

function getFormatter(lang?: string, options?: Intl.NumberFormatOptions): Intl.NumberFormat {
  const locale = getNumberLocale(lang)
  const key = `${locale}:${JSON.stringify(options ?? {})}`
  if (!formatters.has(key)) {
    formatters.set(key, new Intl.NumberFormat(locale, options))
  }
  return formatters.get(key)!
}

function getEgpFormatter(lang?: string): Intl.NumberFormat {
  const locale = getNumberLocale(lang)
  if (!egpFormatters.has(locale)) {
    egpFormatters.set(
      locale,
      new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: 'EGP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }),
    )
  }
  return egpFormatters.get(locale)!
}

export function formatNumber(amount: number | string | null | undefined, lang?: string): string {
  const n = Number(amount ?? 0)
  if (Number.isNaN(n)) return getFormatter(lang).format(0)
  return getFormatter(lang, { maximumFractionDigits: 2 }).format(n)
}

export function formatInteger(amount: number | string | null | undefined, lang?: string): string {
  const n = Number(amount ?? 0)
  if (Number.isNaN(n)) return getFormatter(lang, { maximumFractionDigits: 0 }).format(0)
  return getFormatter(lang, { maximumFractionDigits: 0 }).format(n)
}

export function formatEGP(amount: number | string | null | undefined, lang?: string): string {
  const n = Number(amount ?? 0)
  if (Number.isNaN(n)) return getEgpFormatter(lang).format(0)
  return getEgpFormatter(lang).format(n)
}

const EASTERN_DIGITS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']

/** Convert Western digits in any string to Arabic-Indic when UI is Arabic. */
export function localizeDigits(text: string, lang?: string): string {
  if (!text) return ''
  const l = lang ?? i18n.language ?? 'ar'
  if (!l.startsWith('ar')) return text
  return text.replace(/\d/g, (d) => EASTERN_DIGITS[parseInt(d, 10)])
}

/** Display phone with locale digits; keep raw value for tel:/wa.me links. */
export function formatPhoneDisplay(phone: string, lang?: string): string {
  return localizeDigits(phone, lang)
}
