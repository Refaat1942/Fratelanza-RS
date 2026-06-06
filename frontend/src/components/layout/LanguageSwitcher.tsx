import { useTranslation } from 'react-i18next'
import { Globe } from 'lucide-react'

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ar' ? 'en' : 'ar'
    i18n.changeLanguage(newLang)
    localStorage.setItem('language', newLang)
    document.documentElement.lang = newLang
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr'
  }

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
      title={t('language')}
    >
      <Globe className="h-4 w-4" />
      <span>{i18n.language === 'ar' ? 'EN' : 'عربي'}</span>
    </button>
  )
}
