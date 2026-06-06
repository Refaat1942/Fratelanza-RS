import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import ar from './locales/ar/translation.json'
import en from './locales/en/translation.json'

const savedLang = localStorage.getItem('language') || 'ar'

i18n.use(initReactI18next).init({
  resources: {
    ar: { translation: ar },
    en: { translation: en },
  },
  lng: savedLang,
  fallbackLng: 'ar',
  interpolation: { escapeValue: false },
})

i18n.services.formatter?.add('number', (value, lng) => {
  const locale = lng?.startsWith('ar') ? 'ar-EG' : 'en-US'
  const n = Number(value)
  if (Number.isNaN(n)) return String(value)
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(n)
})

export default i18n
