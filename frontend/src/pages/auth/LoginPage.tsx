import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Building2 } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

export function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data: tokens } = await api.post('/auth/login', { email, password })
      const { data: user } = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      })
      setAuth(tokens.access_token, tokens.refresh_token, user)
      navigate(user.is_super_admin ? '/super-admin' : '/dashboard')
    } catch {
      setError(t('invalid_credentials'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen">
      <div className="hidden w-1/2 bg-gradient-to-br from-primary-900 via-primary-800 to-primary-950 lg:flex lg:flex-col lg:justify-center lg:p-16">
        <Building2 className="mb-8 h-16 w-16 text-accent-500" />
        <h1 className="text-4xl font-bold text-white">{t('platform_full')}</h1>
        <p className="mt-4 text-lg text-primary-200">{t('login_subtitle')}</p>
        <div className="mt-12 grid grid-cols-2 gap-4 text-sm text-primary-200">
          <div className="rounded-lg bg-white/10 p-4">ERP & CRM</div>
          <div className="rounded-lg bg-white/10 p-4">Property Management</div>
          <div className="rounded-lg bg-white/10 p-4">Construction</div>
          <div className="rounded-lg bg-white/10 p-4">Finance & BI</div>
        </div>
      </div>
      <div className="flex flex-1 flex-col justify-center px-8 lg:px-16">
        <div className="absolute end-8 top-8">
          <LanguageSwitcher />
        </div>
        <div className="mx-auto w-full max-w-md">
          <h2 className="text-2xl font-bold text-slate-900">{t('login')}</h2>
          <p className="mt-2 text-slate-500">{t('login_subtitle')}</p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <Input
              label={t('email')}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
            <Input
              label={t('password')}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" loading={loading} className="w-full">
              {loading ? t('signing_in') : t('login')}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
