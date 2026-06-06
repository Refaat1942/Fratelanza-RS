import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Upload } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/lib/api'

const API_URL = import.meta.env.VITE_API_URL || ''

export function BrandingPage() {
  const { t, i18n } = useTranslation()
  const { company, fetchCompany, setCompany } = useCompanyStore()
  const [form, setForm] = useState({ name_ar: '', name_en: '', phone: '', city: '', currency: 'EGP' })
  const [loading, setLoading] = useState(false)

  useEffect(() => { fetchCompany() }, [fetchCompany])

  useEffect(() => {
    if (company) {
      setForm({
        name_ar: company.name_ar,
        name_en: company.name_en,
        phone: '',
        city: company.city || '',
        currency: company.currency || 'EGP',
      })
    }
  }, [company])

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.put('/companies/me/branding', form)
      setCompany(data)
    } finally {
      setLoading(false)
    }
  }

  const uploadLogo = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    const { data } = await api.post('/companies/me/logo', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    setCompany(data)
  }

  const logoSrc = company?.logo_url
    ? (company.logo_url.startsWith('http') ? company.logo_url : `${API_URL}${company.logo_url}`)
    : null

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-slate-900">{t('branding')}</h1>
      <p className="mb-6 text-sm text-slate-500">{t('branding_subtitle')}</p>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 font-semibold">{t('company_logo')}</h2>
          <div className="flex items-center gap-6">
            {logoSrc ? (
              <img src={logoSrc} alt="Logo" className="h-20 w-20 rounded-xl border object-contain" />
            ) : (
              <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-primary-700 text-2xl font-bold text-white">
                {(company?.name_en || 'F').charAt(0)}
              </div>
            )}
            <label className="cursor-pointer">
              <input type="file" accept="image/*" className="hidden" onChange={uploadLogo} />
              <span className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50">
                <Upload className="h-4 w-4" />{t('upload_logo')}
              </span>
            </label>
          </div>
        </Card>

        <Card>
          <form onSubmit={save} className="space-y-4">
            <h2 className="font-semibold">{t('company_details')}</h2>
            <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} required />
            <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
            <Input label={t('city')} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            <div>
              <label className="mb-1 block text-sm font-medium">{t('currency')}</label>
              <select className="input-field" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })}>
                <option value="EGP">EGP — Egyptian Pound (ج.م)</option>
              </select>
            </div>
            <p className="rounded-lg bg-blue-50 p-3 text-xs text-blue-800">{t('tenant_isolation_note')}</p>
            <Button type="submit" loading={loading}>{t('save')}</Button>
          </form>
        </Card>
      </div>

      {company && (
        <Card className="mt-6">
          <p className="text-sm text-slate-600">
            {t('preview')}: <strong>{i18n.language === 'ar' ? company.name_ar : company.name_en}</strong>
            {' · '}{company.code} · {company.currency || 'EGP'}
          </p>
        </Card>
      )}
    </div>
  )
}
