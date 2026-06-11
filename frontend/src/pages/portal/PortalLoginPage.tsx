import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Building2, Home, Receipt, HardHat } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

const HIGHLIGHTS = [
  { icon: Receipt, labelKey: 'portal_highlight_receipts' },
  { icon: Home, labelKey: 'portal_highlight_installments' },
  { icon: HardHat, labelKey: 'portal_highlight_progress' },
] as const

export function PortalLoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data: tokens } = await api.post('/auth/login', { username, password })
      const { data: user } = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      })
      if (user.system_role !== 'customer' && !user.is_super_admin) {
        setError(t('portal_staff_login_hint'))
        return
      }
      setAuth(tokens.access_token, tokens.refresh_token, user)
      navigate('/portal')
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string }
      const detail = ax.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : t('invalid_credentials')
      setError(msg === 'trial_expired' ? t('trial_expired_login') : msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute -start-32 -top-32 h-96 w-96 rounded-full bg-primary-400/20 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 end-0 h-80 w-80 rounded-full bg-emerald-400/15 blur-3xl" />

      <div className="relative hidden w-1/2 flex-col justify-center bg-gradient-to-br from-primary-900 via-primary-800 to-emerald-900 p-16 lg:flex">
        <Building2 className="mb-8 h-14 w-14 text-emerald-300" />
        <h1 className="text-4xl font-bold text-white">{t('portal_title')}</h1>
        <p className="mt-4 max-w-md text-lg text-primary-100">{t('portal_login_subtitle')}</p>
        <ul className="mt-12 space-y-4">
          {HIGHLIGHTS.map(({ icon: Icon, labelKey }) => (
            <li key={labelKey} className="flex items-center gap-3 text-primary-50">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10">
                <Icon className="h-4 w-4" />
              </span>
              {t(labelKey)}
            </li>
          ))}
        </ul>
      </div>

      <div className="relative flex flex-1 flex-col justify-center px-8 lg:px-16">
        <div className="absolute end-8 top-8">
          <LanguageSwitcher />
        </div>
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Building2 className="mb-4 h-12 w-12 text-primary-600" />
            <h1 className="text-2xl font-bold text-primary-900">{t('portal_title')}</h1>
          </div>
          <div className="card card-gradient-border">
            <h2 className="text-2xl font-bold text-slate-900">{t('portal_sign_in')}</h2>
            <p className="mt-2 text-slate-500">{t('portal_login_help')}</p>
            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              <Input
                label={t('username')}
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder="buyer@demo.fratelanza.com"
              />
              <Input
                label={t('password')}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              {error && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
              )}
              <Button type="submit" loading={loading} className="w-full">
                {loading ? t('signing_in') : t('portal_sign_in')}
              </Button>
            </form>
            <p className="mt-6 text-center text-sm text-slate-500">
              {t('portal_staff_link')}{' '}
              <Link to="/login" className="font-medium text-primary-700 hover:underline">
                {t('login')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
