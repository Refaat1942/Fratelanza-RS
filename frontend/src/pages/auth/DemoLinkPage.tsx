import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { FlaskConical, ShieldAlert } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { useModulesStore } from '@/stores/modulesStore'
import { usePermissionsStore } from '@/stores/permissionsStore'

/** Password-less entry to a customer demo: /demo/<token>. Works only until the demo's end date. */
export function DemoLinkPage() {
  const { token } = useParams()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const logout = useAuthStore((s) => s.logout)
  const clearModules = useModulesStore((s) => s.clear)
  const clearPermissions = usePermissionsStore((s) => s.clear)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      logout()
      clearModules()
      clearPermissions()
      try {
        const { data: tokens } = await api.post('/auth/demo-link', { token })
        const { data: user } = await api.get('/auth/me', { headers: { Authorization: `Bearer ${tokens.access_token}` } })
        if (cancelled) return
        setAuth(tokens.access_token, tokens.refresh_token, user)
        navigate('/dashboard', { replace: true })
      } catch (err) {
        const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
        if (!cancelled) setError(typeof detail === 'string' && detail.startsWith('demo_') ? detail : 'demo_link_invalid')
      }
    })()
    return () => { cancelled = true }
  }, [token, setAuth, logout, clearModules, clearPermissions, navigate])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-violet-50 to-primary-50 p-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-lg">
        {error ? (
          <>
            <ShieldAlert className="mx-auto mb-4 h-12 w-12 text-amber-500" />
            <p className="text-lg font-semibold text-slate-900">{t(`re.errors.${error}`)}</p>
            <p className="mt-2 text-sm text-slate-500">{t('re.demos.link_contact')}</p>
          </>
        ) : (
          <>
            <FlaskConical className="mx-auto mb-4 h-12 w-12 animate-pulse text-violet-600" />
            <p className="text-lg font-semibold text-slate-900">{t('re.demos.opening')}</p>
          </>
        )}
      </div>
    </div>
  )
}
