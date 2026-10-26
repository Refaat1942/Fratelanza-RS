import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Clock, AlertTriangle } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

interface MeResponse {
  payment_status?: string
  trial_days_remaining?: number | null
  trial_end_date?: string | null
  company_status?: string
}

export function TrialBanner() {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const setAuth = useAuthStore((s) => s.setAuth)
  const accessToken = useAuthStore((s) => s.accessToken)
  const refreshToken = useAuthStore((s) => s.refreshToken)

  const userId = user?.id
  const isSuperAdmin = user?.is_super_admin
  useEffect(() => {
    // Refresh billing/trial fields once per session token. Depending on `user` itself re-ran this
    // effect after every setAuth (new object) and called /auth/me in an endless loop.
    if (!accessToken || !userId || isSuperAdmin) return
    api.get<MeResponse>('/auth/me').then(({ data }) => {
      const current = useAuthStore.getState().user
      if (current && refreshToken) {
        setAuth(accessToken, refreshToken, { ...current, ...data } as typeof current)
      }
    }).catch(() => {})
  }, [accessToken, refreshToken, setAuth, userId, isSuperAdmin])

  const me = user as MeResponse | null
  if (!me || me.payment_status !== 'trial') return null

  const days = me.trial_days_remaining
  if (days == null) return null

  const urgent = days <= 3

  return (
    <div
      className={`border-b px-4 py-2.5 text-sm ${
        urgent
          ? 'border-amber-300 bg-amber-50 text-amber-900'
          : 'border-blue-200 bg-blue-50 text-blue-900'
      }`}
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-2 text-center sm:justify-start sm:text-start">
        {urgent ? <AlertTriangle className="h-4 w-4 shrink-0" /> : <Clock className="h-4 w-4 shrink-0" />}
        <span>
          {days === 0
            ? t('trial_ends_today')
            : t('trial_days_left', { count: days })}
          {me.trial_end_date && (
            <span className="ms-1 opacity-80">
              ({t('trial_ends')}: {me.trial_end_date})
            </span>
          )}
        </span>
        <span className="hidden text-xs opacity-75 sm:inline">— {t('trial_help')}</span>
      </div>
    </div>
  )
}
