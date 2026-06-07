import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Building2, Sparkles } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

const FEATURES = [
  { label: 'ERP & CRM', color: 'from-blue-500/30 to-cyan-500/20' },
  { label: 'Property Management', color: 'from-violet-500/30 to-purple-500/20' },
  { label: 'Construction', color: 'from-amber-500/30 to-orange-500/20' },
  { label: 'Finance & BI', color: 'from-emerald-500/30 to-teal-500/20' },
]

export function LoginPage() {
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
      setAuth(tokens.access_token, tokens.refresh_token, user)
      navigate(user.is_super_admin ? '/super-admin' : '/dashboard')
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string }; status?: number }; message?: string }
      const detail = ax.response?.data?.detail
      if (detail) {
        setError(typeof detail === 'string' ? detail : t('invalid_credentials'))
      } else if (!ax.response) {
        setError('Cannot reach server. Check your connection or contact support.')
      } else {
        setError(t('invalid_credentials'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute -start-32 -top-32 h-96 w-96 rounded-full bg-primary-400/20 blur-3xl animate-float-slow" />
      <div className="pointer-events-none absolute bottom-0 end-0 h-80 w-80 rounded-full bg-violet-400/20 blur-3xl animate-float-slower" />

      <div className="relative hidden w-1/2 overflow-hidden bg-gradient-to-br from-primary-950 via-primary-800 to-primary-900 lg:flex lg:flex-col lg:justify-center lg:p-16">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMtOS45NDEgMC0xOCA4LjA1OS0xOCAxOHM4LjA1OSAxOCAxOCAxOCAxOC04LjA1OSAxOC0xOC04LjA1OS0xOC0xOC0xOHoiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii4wNiIvPjwvZz48L3N2Zz4=')] opacity-50" />
        <Building2 className="relative mb-8 h-16 w-16 text-accent-500 animate-float-slow" />
        <h1 className="relative text-4xl font-bold text-white">{t('platform_full')}</h1>
        <p className="relative mt-4 text-lg text-primary-200">{t('login_subtitle')}</p>
        <div className="relative mt-12 grid grid-cols-2 gap-4 text-sm">
          {FEATURES.map((f, i) => (
            <div
              key={f.label}
              className={`login-feature-card bg-gradient-to-br ${f.color}`}
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              <Sparkles className="mb-2 h-4 w-4 text-accent-400" />
              {f.label}
            </div>
          ))}
        </div>
      </div>

      <div className="relative flex flex-1 flex-col justify-center px-8 lg:px-16">
        <div className="absolute end-8 top-8">
          <LanguageSwitcher />
        </div>
        <div className="mx-auto w-full max-w-md animate-fade-in-up">
          <div className="mb-8 lg:hidden">
            <Building2 className="mb-4 h-12 w-12 text-primary-600" />
            <h1 className="text-2xl font-bold text-primary-900">{t('platform_full')}</h1>
          </div>
          <div className="card card-gradient-border">
            <h2 className="text-2xl font-bold text-slate-900">{t('login')}</h2>
            <p className="mt-2 text-slate-500">{t('login_subtitle')}</p>
            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              <Input
                label={t('username')}
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder="demo_admin"
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
                <p className="animate-fade-in rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
              )}
              <Button type="submit" loading={loading} className="w-full">
                {loading ? t('signing_in') : t('login')}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
