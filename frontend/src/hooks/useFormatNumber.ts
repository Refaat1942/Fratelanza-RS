import { useTranslation } from 'react-i18next'
import { formatEGP, formatInteger, formatNumber, formatPhoneDisplay, localizeDigits } from '@/lib/currency'

export function useFormatNumber() {
  const { i18n } = useTranslation()
  const lang = i18n.language
  return {
    lang,
    formatNumber: (v: number | string | null | undefined) => formatNumber(v, lang),
    formatInteger: (v: number | string | null | undefined) => formatInteger(v, lang),
    formatEGP: (v: number | string | null | undefined) => formatEGP(v, lang),
    formatPhone: (v: string) => formatPhoneDisplay(v, lang),
    localizeDigits: (v: string) => localizeDigits(v, lang),
  }
}
